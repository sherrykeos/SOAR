import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import docx
import fitz

from app.models.adapter import ModelCapability
from app.models.manager import ModelManager
from app.models.mock import MockModel
from app.models.registry import ModelRegistry
from app.models.router import ModelRouter
from app.orchestrator.agent import Agent, AgentState, TaskContext
from app.orchestrator.execution import Executor, ToolAction
from app.orchestrator.planning import Planner
from app.tools.base import BaseTool
from app.tools.docx_creator import DOCXCreatorTool
from app.tools.pdf_reader import PDFReaderTool
from app.tools.read_file import ReadFileTool
from app.tools.registry import ToolRegistry
from app.tools.validator import ToolValidator, ValidationResult


class TestAgentArgumentReliability(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.inputs_dir = os.path.join(self.test_dir, "inputs").replace("\\", "/")
        self.outputs_dir = os.path.join(self.test_dir, "outputs").replace("\\", "/")
        os.makedirs(self.inputs_dir, exist_ok=True)
        os.makedirs(self.outputs_dir, exist_ok=True)

        # Create a sample PDF file inside inputs/
        self.sample_pdf = f"{self.inputs_dir}/inspection_report.pdf"
        doc = fitz.open()
        p = doc.new_page()
        p.insert_text((72, 72), "Turbine Safety Inspection: Temperature 85C, Pressure 120 PSI. Status: APPROVED")
        doc.save(self.sample_pdf)
        doc.close()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    # -------------------------------------------------------------
    # Scenario 1: Missing required argument validation
    # -------------------------------------------------------------
    def test_missing_required_argument_validation(self):
        tool = PDFReaderTool()
        val_result = ToolValidator.validate(tool, {})
        self.assertFalse(val_result.is_valid)
        self.assertEqual(val_result.error_code, "missing_argument")
        self.assertEqual(val_result.argument, "file_path")
        self.assertIn("Missing required parameter 'file_path'", val_result.error_message)

        # Confirm tool does not execute and returns structured error from Executor
        registry = ToolRegistry()
        registry.register(tool)
        executor = Executor(tool_registry=registry)
        action = ToolAction(tool="pdf_reader", arguments={})
        res = executor.execute_action(action)
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error_code"], "missing_argument")
        self.assertIn("Tool action validation failed", res["error"])

    # -------------------------------------------------------------
    # Scenario 2: Unknown argument / placeholder detection
    # -------------------------------------------------------------
    def test_unknown_or_placeholder_argument_detection(self):
        tool = PDFReaderTool()
        # Test placeholder key 'parameter_name'
        placeholder_val = ToolValidator.validate(tool, {"parameter_name": "file_path"})
        self.assertFalse(placeholder_val.is_valid)
        self.assertEqual(placeholder_val.error_code, "placeholder_key_detected")
        self.assertIn("parameter_name", placeholder_val.error_message)

        # Test random unknown key
        unknown_val = ToolValidator.validate(tool, {"random_unknown_key": "some_value"})
        self.assertFalse(unknown_val.is_valid)
        self.assertEqual(unknown_val.error_code, "unknown_argument")
        self.assertIn("Allowed parameters", unknown_val.error_message)

    # -------------------------------------------------------------
    # Scenario 3: Exact path preservation in TaskContext
    # -------------------------------------------------------------
    def test_exact_path_preservation(self):
        task_str = "Read inputs/inspection_report.pdf, analyze its contents, and create an approval note as outputs/approval_note.docx."
        ctx = TaskContext.from_task(task_str)

        self.assertEqual(ctx.original_task, task_str)
        self.assertIn("inputs/inspection_report.pdf", ctx.detected_paths)
        self.assertIn("outputs/approval_note.docx", ctx.detected_paths)
        self.assertIn("inputs/inspection_report.pdf", ctx.input_paths)
        self.assertIn("outputs/approval_note.docx", ctx.output_paths)

        # Verify planner prompt includes the detected exact paths
        registry = ToolRegistry()
        registry.register(PDFReaderTool())
        registry.register(DOCXCreatorTool())
        mock_model = MockModel(
            model_id="mock-path-test",
            capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
            fixed_response=json.dumps({"status": "complete", "steps": []}),
        )
        reg = ModelRegistry()
        reg.register(mock_model)
        mgr = ModelManager(model_registry=reg, model_router=ModelRouter(reg))
        planner = Planner(model_manager=mgr, tool_registry=registry)

        state = AgentState(task=task_str, context=ctx)
        context_str = planner._format_task_context(state)
        self.assertIn("inputs/inspection_report.pdf", context_str)
        self.assertIn("outputs/approval_note.docx", context_str)
        self.assertIn("CRITICAL", context_str)

    # -------------------------------------------------------------
    # Scenario 4: File-not-found observation & recovery
    # -------------------------------------------------------------
    def test_file_not_found_correction(self):
        class CorrectionResponder:
            def __init__(self, full_pdf_path: str):
                self.count = 0
                self.full_pdf_path = full_pdf_path

            def __call__(self, prompt: str) -> str:
                self.count += 1
                if self.count == 1:
                    # Model makes a mistake: tries bad filename
                    return json.dumps({
                        "status": "continue",
                        "thought": "Trying without full path first.",
                        "steps": [{"tool": "pdf_reader", "arguments": {"file_path": "wrong_non_existent.pdf"}}]
                    })
                elif self.count == 2:
                    # Model receives error observation and fixes path
                    return json.dumps({
                        "status": "continue",
                        "thought": "Fixing path to exact path from task context.",
                        "steps": [{"tool": "pdf_reader", "arguments": {"file_path": self.full_pdf_path}}]
                    })
                else:
                    return json.dumps({
                        "status": "complete",
                        "thought": "File read successfully. Done.",
                        "steps": []
                    })

        mock_model = MockModel(
            model_id="mock-recovery-agent",
            capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
            response_fn=CorrectionResponder(self.sample_pdf),
        )
        model_registry = ModelRegistry()
        model_registry.register(mock_model)
        model_manager = ModelManager(model_registry=model_registry, model_router=ModelRouter(model_registry))

        tool_registry = ToolRegistry()
        tool_registry.register(PDFReaderTool())

        planner = Planner(model_manager=model_manager, tool_registry=tool_registry)
        executor = Executor(tool_registry=tool_registry)
        agent = Agent(planner=planner, executor=executor, max_iterations=5)

        state = agent.run(f"Read {self.sample_pdf} and verify systems.")
        self.assertEqual(state.status, "completed")
        self.assertEqual(state.iterations, 3)
        self.assertEqual(len(state.observations), 2)
        self.assertEqual(state.observations[0]["status"], "error")
        self.assertIn("File not found", state.observations[0]["result"])
        self.assertEqual(state.observations[1]["status"], "completed")
        self.assertIn("Turbine Safety Inspection", state.observations[1]["result"])

    # -------------------------------------------------------------
    # Scenario 5: Repeated failure fingerprinting detection
    # -------------------------------------------------------------
    def test_repeated_failure_detection(self):
        class LoopingBadResponder:
            def __init__(self):
                self.count = 0

            def __call__(self, prompt: str) -> str:
                self.count += 1
                # Planner keeps generating the exact same failing action
                return json.dumps({
                    "status": "continue",
                    "thought": "Trying the same bad tool call again.",
                    "steps": [{"tool": "pdf_reader", "arguments": {"parameter_name": "file_path"}}]
                })

        mock_model = MockModel(
            model_id="mock-looping-agent",
            capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
            response_fn=LoopingBadResponder(),
        )
        model_registry = ModelRegistry()
        model_registry.register(mock_model)
        model_manager = ModelManager(model_registry=model_registry, model_router=ModelRouter(model_registry))

        tool_registry = ToolRegistry()
        tool_registry.register(PDFReaderTool())

        planner = Planner(model_manager=model_manager, tool_registry=tool_registry)
        executor = Executor(tool_registry=tool_registry)
        agent = Agent(planner=planner, executor=executor, max_iterations=4)

        state = agent.run("Process file with repeating bad tool call.")
        # Verify repeated failure was caught and marked as repeated failure
        self.assertGreaterEqual(len(state.observations), 2)
        second_obs = state.observations[1]
        self.assertIn("REPEATED FAILING ACTION DETECTED", second_obs["result"])

    # -------------------------------------------------------------
    # Scenario 6: Successful validation recovery
    # -------------------------------------------------------------
    def test_successful_validation_recovery(self):
        class ValidationRecoveryResponder:
            def __init__(self, valid_pdf: str):
                self.count = 0
                self.valid_pdf = valid_pdf

            def __call__(self, prompt: str) -> str:
                self.count += 1
                if self.count == 1:
                    # Missing required argument
                    return json.dumps({
                        "status": "continue",
                        "thought": "Empty arguments by mistake.",
                        "steps": [{"tool": "pdf_reader", "arguments": {}}]
                    })
                elif self.count == 2:
                    # Recovers from validation error
                    return json.dumps({
                        "status": "continue",
                        "thought": "Providing required file_path parameter.",
                        "steps": [{"tool": "pdf_reader", "arguments": {"file_path": self.valid_pdf}}]
                    })
                else:
                    return json.dumps({
                        "status": "complete",
                        "thought": "Task finished successfully.",
                        "steps": []
                    })

        mock_model = MockModel(
            model_id="mock-val-recovery",
            capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
            response_fn=ValidationRecoveryResponder(self.sample_pdf),
        )
        model_registry = ModelRegistry()
        model_registry.register(mock_model)
        model_manager = ModelManager(model_registry=model_registry, model_router=ModelRouter(model_registry))

        tool_registry = ToolRegistry()
        tool_registry.register(PDFReaderTool())

        planner = Planner(model_manager=model_manager, tool_registry=tool_registry)
        executor = Executor(tool_registry=tool_registry)
        agent = Agent(planner=planner, executor=executor, max_iterations=5)

        state = agent.run(f"Extract information from {self.sample_pdf}")
        self.assertEqual(state.status, "completed")
        self.assertEqual(state.iterations, 3)
        self.assertIn("Missing required parameter 'file_path'", state.observations[0]["result"])
        self.assertEqual(state.observations[1]["status"], "completed")
        self.assertIn("Turbine Safety Inspection", state.observations[1]["result"])

    # -------------------------------------------------------------
    # Scenario 7: Original workflow regression
    # (inputs/inspection_report.pdf -> outputs/approval_note.docx)
    # -------------------------------------------------------------
    def test_original_workflow_regression(self):
        out_docx_path = f"{self.outputs_dir}/approval_note.docx"

        class EndToEndWorkflowResponder:
            def __init__(self, in_pdf: str, out_docx: str):
                self.count = 0
                self.in_pdf = in_pdf
                self.out_docx = out_docx

            def __call__(self, prompt: str) -> str:
                self.count += 1
                if self.count == 1:
                    # Model starts with bad parameter name first
                    return json.dumps({
                        "status": "continue",
                        "thought": "Attempting bad tool call.",
                        "steps": [{"tool": "pdf_reader", "arguments": {"parameter_name": "file_path"}}]
                    })
                elif self.count == 2:
                    # Fixes tool call to read PDF
                    return json.dumps({
                        "status": "continue",
                        "thought": "Fixing parameter to file_path with exact path from task.",
                        "steps": [{"tool": "pdf_reader", "arguments": {"file_path": self.in_pdf}}]
                    })
                elif self.count == 3:
                    # Creates approval note DOCX
                    return json.dumps({
                        "status": "continue",
                        "thought": "Creating approval note DOCX based on extracted PDF results.",
                        "steps": [
                            {
                                "tool": "docx_creator",
                                "arguments": {
                                    "output_path": self.out_docx,
                                    "title": "Industrial Turbine Approval Note",
                                    "content": "Inspection completed. Status is APPROVED. Pressure 120 PSI, Temperature 85C.",
                                }
                            }
                        ]
                    })
                else:
                    return json.dumps({
                        "status": "complete",
                        "thought": "Approval note created. Workflow complete.",
                        "steps": []
                    })

        mock_model = MockModel(
            model_id="mock-e2e-workflow",
            capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
            response_fn=EndToEndWorkflowResponder(self.sample_pdf, out_docx_path),
        )
        model_registry = ModelRegistry()
        model_registry.register(mock_model)
        model_manager = ModelManager(model_registry=model_registry, model_router=ModelRouter(model_registry))

        tool_registry = ToolRegistry()
        tool_registry.register(PDFReaderTool())
        tool_registry.register(DOCXCreatorTool())

        planner = Planner(model_manager=model_manager, tool_registry=tool_registry)
        executor = Executor(tool_registry=tool_registry)
        agent = Agent(planner=planner, executor=executor, max_iterations=6)

        task_desc = f"Read {self.sample_pdf}, analyze its contents, and create an approval note as {out_docx_path}."
        state = agent.run(task_desc)

        self.assertEqual(state.status, "completed")
        self.assertEqual(state.iterations, 4)
        self.assertTrue(os.path.exists(out_docx_path))

        # Inspect generated DOCX content
        doc_gen = docx.Document(out_docx_path)
        texts = [p.text for p in doc_gen.paragraphs]
        self.assertTrue(any("Industrial Turbine Approval Note" in t for t in texts))
        self.assertTrue(any("Pressure 120 PSI" in t for t in texts))


if __name__ == "__main__":
    unittest.main()
