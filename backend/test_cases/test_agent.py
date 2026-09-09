import json
import os
import tempfile
import unittest

import docx
import fitz

from app.models.adapter import ModelCapability
from app.models.manager import ModelManager
from app.models.mock import MockModel
from app.models.registry import ModelRegistry
from app.models.router import ModelRouter
from app.orchestrator.agent import Agent
from app.orchestrator.execution import Executor
from app.orchestrator.planning import Planner
from app.tools.base import BaseTool
from app.tools.docx_creator import DOCXCreatorTool
from app.tools.pdf_reader import PDFReaderTool
from app.tools.read_file import ReadFileTool
from app.tools.registry import ToolRegistry


class TestAgentLoop(unittest.TestCase):

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".txt")
        self.temp_path = self.temp_file.name.replace("\\", "/")
        self.temp_file.write("SOAR Inspection Report: ALL SYSTEMS OPERATIONAL")
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_path):
            os.remove(self.temp_path)

    def test_deterministic_multi_turn_loop(self):
        class SequenceResponder:
            def __init__(self, file_path: str):
                self.count = 0
                self.file_path = file_path

            def __call__(self, prompt: str) -> str:
                self.count += 1
                if self.count == 1:
                    return json.dumps({
                        "status": "continue",
                        "thought": "I need to read the inspection file first.",
                        "steps": [{"tool": "read_file", "arguments": {"file_path": self.file_path}}]
                    })
                else:
                    return json.dumps({
                        "status": "complete",
                        "thought": "Inspection file has been read and verified. Task complete.",
                        "steps": []
                    })

        mock_responder = SequenceResponder(self.temp_path)
        mock_model = MockModel(
            model_id="mock-agent-reasoner",
            capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
            priority=1,
            response_fn=mock_responder,
        )

        model_registry = ModelRegistry()
        model_registry.register(mock_model)
        model_router = ModelRouter(model_registry, default_model_id="mock-agent-reasoner")
        model_manager = ModelManager(model_registry=model_registry, model_router=model_router)

        tool_registry = ToolRegistry()
        tool_registry.register(ReadFileTool())

        planner = Planner(model_manager=model_manager, tool_registry=tool_registry)
        executor = Executor(tool_registry=tool_registry)
        agent = Agent(planner=planner, executor=executor, max_iterations=5)

        final_state = agent.run("Read and verify the inspection report.")

        self.assertEqual(final_state.status, "completed")
        self.assertEqual(final_state.iterations, 2)
        self.assertEqual(len(final_state.observations), 1)
        self.assertEqual(final_state.observations[0]["tool"], "read_file")
        self.assertEqual(final_state.observations[0]["result"], "SOAR Inspection Report: ALL SYSTEMS OPERATIONAL")

    def test_unknown_tool_rejection(self):
        evil_mock = MockModel(
            model_id="evil-mock",
            capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
            fixed_response=json.dumps({
                "status": "continue",
                "steps": [{"tool": "evil_tool", "arguments": {}}]
            })
        )
        evil_registry = ModelRegistry()
        evil_registry.register(evil_mock)
        evil_mgr = ModelManager(model_registry=evil_registry, model_router=ModelRouter(evil_registry))
        tool_reg = ToolRegistry()
        tool_reg.register(ReadFileTool())
        evil_planner = Planner(model_manager=evil_mgr, tool_registry=tool_reg)
        evil_agent = Agent(planner=evil_planner, executor=Executor(tool_registry=tool_reg), max_iterations=3)

        evil_state = evil_agent.run("Do something malicious.")
        self.assertEqual(evil_state.status, "error")
        self.assertIn("Unknown tool 'evil_tool'", evil_state.results[0]["error"])

    def test_malformed_plan_handling(self):
        broken_mock = MockModel(
            model_id="broken-mock",
            capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
            fixed_response="I cannot output JSON today!",
        )
        broken_registry = ModelRegistry()
        broken_registry.register(broken_mock)
        broken_mgr = ModelManager(model_registry=broken_registry, model_router=ModelRouter(broken_registry))
        tool_reg = ToolRegistry()
        broken_planner = Planner(model_manager=broken_mgr, tool_registry=tool_reg)
        broken_agent = Agent(planner=broken_planner, executor=Executor(tool_registry=tool_reg), max_iterations=3)

        broken_state = broken_agent.run("Test invalid JSON.")
        self.assertEqual(broken_state.status, "error")
        self.assertIn("Plan parsing/validation failed", broken_state.results[0]["error"])

    def test_infinite_loop_protection(self):
        infinite_mock = MockModel(
            model_id="infinite-mock",
            capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
            fixed_response=json.dumps({
                "status": "continue",
                "steps": [{"tool": "read_file", "arguments": {"file_path": self.temp_path}}]
            })
        )
        inf_registry = ModelRegistry()
        inf_registry.register(infinite_mock)
        inf_mgr = ModelManager(model_registry=inf_registry, model_router=ModelRouter(inf_registry))
        tool_reg = ToolRegistry()
        tool_reg.register(ReadFileTool())
        inf_planner = Planner(model_manager=inf_mgr, tool_registry=tool_reg)
        inf_agent = Agent(planner=inf_planner, executor=Executor(tool_registry=tool_reg), max_iterations=3)

        inf_state = inf_agent.run("Loop forever.")
        self.assertEqual(inf_state.status, "max_iterations_reached")
        self.assertEqual(inf_state.iterations, 3)

    def test_tool_runtime_failure_handling(self):
        class CrashingTool(BaseTool):
            @property
            def name(self) -> str:
                return "crashing_tool"

            @property
            def description(self) -> str:
                return "A tool that crashes on execution."

            def execute(self, **kwargs):
                raise RuntimeError("Database connection lost")

        crash_tool_registry = ToolRegistry()
        crash_tool_registry.register(CrashingTool())

        crash_mock = MockModel(
            model_id="crash-mock",
            capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
            fixed_response=json.dumps({
                "status": "continue",
                "steps": [{"tool": "crashing_tool", "arguments": {}}]
            })
        )
        crash_reg = ModelRegistry()
        crash_reg.register(crash_mock)
        crash_mgr = ModelManager(model_registry=crash_reg, model_router=ModelRouter(crash_reg))
        crash_planner = Planner(model_manager=crash_mgr, tool_registry=crash_tool_registry)
        crash_executor = Executor(tool_registry=crash_tool_registry)
        crash_agent = Agent(planner=crash_planner, executor=crash_executor, max_iterations=2)

        crash_state = crash_agent.run("Run crashing tool.")
        self.assertGreater(len(crash_state.observations), 0)
        self.assertEqual(crash_state.observations[0]["status"], "error")
        self.assertIn("Database connection lost", crash_state.observations[0]["result"])

    def test_agent_recovery_from_invalid_tool_arguments(self):
        class RecoverySequenceResponder:
            def __init__(self, file_path: str):
                self.count = 0
                self.file_path = file_path

            def __call__(self, prompt: str) -> str:
                self.count += 1
                if self.count == 1:
                    return json.dumps({
                        "status": "continue",
                        "thought": "I will read the file but with bad parameter name.",
                        "steps": [{"tool": "read_file", "arguments": {"parameter_name": "file_path"}}]
                    })
                elif self.count == 2:
                    return json.dumps({
                        "status": "continue",
                        "thought": "I see the parameter error. Fixing argument to file_path.",
                        "steps": [{"tool": "read_file", "arguments": {"file_path": self.file_path}}]
                    })
                else:
                    return json.dumps({
                        "status": "complete",
                        "thought": "File read successfully after recovery.",
                        "steps": []
                    })

        rec_mock = MockModel(
            model_id="rec-mock",
            capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
            response_fn=RecoverySequenceResponder(self.temp_path),
        )
        rec_reg = ModelRegistry()
        rec_reg.register(rec_mock)
        rec_mgr = ModelManager(model_registry=rec_reg, model_router=ModelRouter(rec_reg))
        rec_tool_reg = ToolRegistry()
        rec_tool_reg.register(ReadFileTool())
        rec_planner = Planner(model_manager=rec_mgr, tool_registry=rec_tool_reg)
        rec_executor = Executor(tool_registry=rec_tool_reg)
        rec_agent = Agent(planner=rec_planner, executor=rec_executor, max_iterations=5)

        rec_state = rec_agent.run("Read inspection report with error recovery.")
        self.assertEqual(rec_state.status, "completed")
        self.assertEqual(rec_state.iterations, 3)
        self.assertEqual(rec_state.observations[0]["status"], "error")
        self.assertIn("Invalid placeholder argument 'parameter_name'", rec_state.observations[0]["result"])
        self.assertEqual(rec_state.observations[1]["status"], "completed")
        self.assertIn("SOAR Inspection Report", rec_state.observations[1]["result"])

    def test_end_to_end_pdf_to_docx_pipeline(self):
        with tempfile.TemporaryDirectory() as pipeline_temp:
            pipeline_dir = pipeline_temp.replace("\\", "/")
            pdf_input = f"{pipeline_dir}/inspection_report.pdf"
            docx_output = f"{pipeline_dir}/approval_note.docx"

            # Create input PDF
            doc = fitz.open()
            p = doc.new_page()
            p.insert_text((72, 72), "Turbine Pressure: 120 PSI. Vibration: Normal. Status: APPROVED")
            doc.save(pdf_input)
            doc.close()

            class PDFToDOCXResponder:
                def __init__(self, in_pdf: str, out_docx: str):
                    self.count = 0
                    self.in_pdf = in_pdf
                    self.out_docx = out_docx

                def __call__(self, prompt: str) -> str:
                    self.count += 1
                    if self.count == 1:
                        return json.dumps({
                            "status": "continue",
                            "thought": "I will read the inspection report PDF first.",
                            "steps": [{"tool": "pdf_reader", "arguments": {"file_path": self.in_pdf}}]
                        })
                    elif self.count == 2:
                        return json.dumps({
                            "status": "continue",
                            "thought": "I will generate the approval note DOCX based on the inspection report.",
                            "steps": [
                                {
                                    "tool": "docx_creator",
                                    "arguments": {
                                        "output_path": self.out_docx,
                                        "title": "Industrial Equipment Approval Note",
                                        "content": "Based on the inspection, Turbine Pressure was 120 PSI and status is APPROVED.",
                                    }
                                }
                            ]
                        })
                    else:
                        return json.dumps({
                            "status": "complete",
                            "thought": "Approval note DOCX has been created. Task complete.",
                            "steps": []
                        })

            p2d_mock = MockModel(
                model_id="p2d-mock",
                capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
                response_fn=PDFToDOCXResponder(pdf_input, docx_output),
            )
            p2d_reg = ModelRegistry()
            p2d_reg.register(p2d_mock)
            p2d_mgr = ModelManager(model_registry=p2d_reg, model_router=ModelRouter(p2d_reg))

            p2d_tool_reg = ToolRegistry()
            p2d_tool_reg.register(PDFReaderTool())
            p2d_tool_reg.register(DOCXCreatorTool())

            p2d_planner = Planner(model_manager=p2d_mgr, tool_registry=p2d_tool_reg)
            p2d_executor = Executor(tool_registry=p2d_tool_reg)
            p2d_agent = Agent(planner=p2d_planner, executor=p2d_executor, max_iterations=5)

            p2d_state = p2d_agent.run(f"Process inspection report at '{pdf_input}' and generate approval note at '{docx_output}'")

            self.assertEqual(p2d_state.status, "completed")
            self.assertEqual(p2d_state.iterations, 3)
            self.assertTrue(os.path.exists(docx_output))

            gen_doc = docx.Document(docx_output)
            doc_texts = [para.text for para in gen_doc.paragraphs]
            self.assertTrue(any("Industrial Equipment Approval Note" in t for t in doc_texts))
            self.assertTrue(any("Turbine Pressure was 120 PSI" in t for t in doc_texts))


if __name__ == "__main__":
    unittest.main()
