import json
import os
import tempfile
from pathlib import Path

import fitz  # PyMuPDF

from app.models.adapter import ModelCapability
from app.models.manager import ModelManager
from app.models.mock import MockModel
from app.models.registry import ModelRegistry
from app.models.router import ModelRouter
from app.orchestrator.agent import Agent
from app.orchestrator.execution import Executor, ToolAction
from app.orchestrator.planning import Planner
from app.tools.pdf_creator import PDFCreatorTool
from app.tools.registry import ToolRegistry


print("[TEST] Starting PDFCreatorTool test suite...\n")

with tempfile.TemporaryDirectory() as temp_dir:
    temp_dir_path = temp_dir.replace("\\", "/")
    output_pdf = f"{temp_dir_path}/test_approval_note.pdf"
    multi_p_pdf = f"{temp_dir_path}/multi_paragraph.pdf"

    # 1. Registration & Retrieval
    print("1 & 2. Testing ToolRegistry registration and retrieval...")
    registry = ToolRegistry()
    registry.register(PDFCreatorTool())

    tool = registry.get("pdf_creator")
    assert tool.name == "pdf_creator"
    assert "PDF" in tool.description
    print(f"Successfully retrieved tool '{tool.name}'.")

    # 2. PDF creation
    print("\n3. Testing PDF creation with title and content...")
    result = tool.execute(
        output_path=output_pdf,
        title="Industrial Plant Safety Approval",
        content="The inspection confirmed all safety systems operate within standard limits.",
    )
    print(f"Execution result: {result}")
    assert "Successfully created" in result
    assert os.path.exists(output_pdf), "PDF file was not created on disk!"
    print("PDF file exists on disk.")

    # 3. Verify PDF structure & contents using PyMuPDF (fitz)
    print("\n4, 5, 6. Verifying created PDF file structure and text with PyMuPDF...")
    doc = fitz.open(output_pdf)
    assert len(doc) >= 1
    extracted_text = doc[0].get_text()
    doc.close()

    print(f"Extracted PDF text:\n{extracted_text}")
    assert "Industrial Plant Safety Approval" in extracted_text
    assert "The inspection confirmed all safety systems" in extracted_text
    print("PDF title and body content verified successfully.")

    # 4. Multi-paragraph support
    print("\n7. Testing multi-paragraph content support...")
    multi_content = (
        "Section 1: Valve integrity inspection complete.\n\n"
        "Section 2: Pipe wall thickness verified.\n\n"
        "Section 3: Approved for operation."
    )
    multi_res = tool.execute(
        output_path=multi_p_pdf,
        title="Comprehensive Mechanical Report",
        content=multi_content,
    )
    assert "Successfully created" in multi_res
    doc_multi = fitz.open(multi_p_pdf)
    multi_text = doc_multi[0].get_text()
    doc_multi.close()

    assert "Section 1" in multi_text
    assert "Section 2" in multi_text
    assert "Section 3" in multi_text
    print("Multi-paragraph PDF generation verified successfully.")

    # 5. Missing parameter & Error handling
    print("\n8. Testing missing parameter handling...")
    missing_res = tool.execute(title="No output path")
    print(f"Missing parameter result: {missing_res}")
    assert "Missing required parameter" in missing_res

    # 6. Executor Integration Test
    print("\n9. Testing execution through Executor...")
    executor = Executor(tool_registry=registry)
    exec_pdf = f"{temp_dir_path}/exec_test.pdf"
    action = ToolAction(
        tool="pdf_creator",
        arguments={
            "output_path": exec_pdf,
            "title": "Executor PDF Note",
            "content": "Generated through Executor.",
        },
    )
    exec_result = executor.execute_action(action)
    print(f"Executor result: {exec_result}")
    assert exec_result["status"] == "completed"
    assert os.path.exists(exec_pdf)
    print("Executor execution verified.")

    # 7. Agent Loop Integration Test
    print("\n10. Testing Agent Loop integration with PDFCreatorTool...")
    agent_pdf = f"{temp_dir_path}/agent_approval.pdf"

    class PDFCreatorSequenceResponder:
        def __init__(self, pdf_path: str):
            self.count = 0
            self.pdf_path = pdf_path

        def __call__(self, prompt: str) -> str:
            self.count += 1
            if self.count == 1:
                return json.dumps({
                    "status": "continue",
                    "thought": "I will create a formal approval note in PDF format.",
                    "steps": [
                        {
                            "tool": "pdf_creator",
                            "arguments": {
                                "output_path": self.pdf_path,
                                "title": "Final Approval Note",
                                "content": "All compliance criteria verified.",
                            }
                        }
                    ]
                })
            else:
                return json.dumps({
                    "status": "complete",
                    "thought": "Approval note PDF has been created. Task complete.",
                    "steps": []
                })

    mock_model = MockModel(
        model_id="mock-pdf-creator-agent",
        capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
        priority=1,
        response_fn=PDFCreatorSequenceResponder(agent_pdf),
    )

    model_registry = ModelRegistry()
    model_registry.register(mock_model)
    model_router = ModelRouter(model_registry, default_model_id="mock-pdf-creator-agent")
    model_manager = ModelManager(model_registry=model_registry, model_router=model_router)

    planner = Planner(model_manager=model_manager, tool_registry=registry)
    agent = Agent(planner=planner, executor=executor, max_iterations=5)

    agent_state = agent.run("Create approval note PDF.")
    print(f"Agent Final Status: {agent_state.status}")
    print(f"Agent Observations: {agent_state.observations}")

    assert agent_state.status == "completed"
    assert agent_state.iterations == 2
    assert os.path.exists(agent_pdf)
    assert agent_state.observations[0]["tool"] == "pdf_creator"
    print("Agent PDF creation integration verified successfully!")

print("\n[TEST] All PDFCreatorTool tests completed successfully!")
