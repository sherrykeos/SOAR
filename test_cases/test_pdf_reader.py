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
from app.orchestrator.action import ToolAction
from app.orchestrator.agent import Agent
from app.orchestrator.executor import Executor
from app.orchestrator.planner import Planner
from app.tools.pdf_reader import PDFReaderTool
from app.tools.registry import ToolRegistry


print("[TEST] Starting PDFReaderTool test suite...\n")

# 1. Create temporary test PDF files dynamically
with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".pdf") as f_valid:
    valid_pdf_path = f_valid.name.replace("\\", "/")

# Write text to valid PDF using PyMuPDF
doc = fitz.open()
page = doc.new_page()
page.insert_text((72, 72), "SOAR Industrial Safety Report\nStatus: PASSED\nInspector: SOAR-Agent-01")
doc.save(valid_pdf_path)
doc.close()

# Create an empty PDF (page without text)
with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".pdf") as f_empty:
    empty_pdf_path = f_empty.name.replace("\\", "/")

doc_empty = fitz.open()
doc_empty.new_page()
doc_empty.save(empty_pdf_path)
doc_empty.close()

# Create a corrupt PDF file
with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".pdf") as f_corrupt:
    corrupt_pdf_path = f_corrupt.name.replace("\\", "/")
    f_corrupt.write(b"Not a valid PDF file content 12345")

print(f"Created temporary valid PDF at: {valid_pdf_path}")
print(f"Created temporary empty PDF at: {empty_pdf_path}")
print(f"Created temporary corrupt PDF at: {corrupt_pdf_path}")

try:
    # ---------------------------------------------------------
    # 1. Registration & Retrieval
    # ---------------------------------------------------------
    print("\n1 & 2. Testing ToolRegistry registration and retrieval...")
    registry = ToolRegistry()
    registry.register(PDFReaderTool())

    tool = registry.get("pdf_reader")
    assert tool.name == "pdf_reader"
    assert "PDF" in tool.description
    print(f"Successfully retrieved tool '{tool.name}'.")

    # ---------------------------------------------------------
    # 2. Extract text from valid PDF
    # ---------------------------------------------------------
    print("\n3. Testing text extraction from valid PDF...")
    extracted_text = tool.execute(file_path=valid_pdf_path)
    print(f"Extracted content:\n--- BEGIN ---\n{extracted_text}\n--- END ---")
    assert "SOAR Industrial Safety Report" in extracted_text
    assert "Status: PASSED" in extracted_text
    print("Valid PDF text extracted successfully.")

    # ---------------------------------------------------------
    # 3. Missing file handling
    # ---------------------------------------------------------
    print("\n4. Testing missing file handling...")
    missing_result = tool.execute(file_path="non_existent_file_soar_999.pdf")
    print(f"Result: {missing_result}")
    assert "File not found" in missing_result
    print("Missing file handled safely.")

    # ---------------------------------------------------------
    # 4. Directory path handling
    # ---------------------------------------------------------
    print("\n5. Testing directory path handling...")
    dir_path = str(Path(valid_pdf_path).parent).replace("\\", "/")
    dir_result = tool.execute(file_path=dir_path)
    print(f"Result: {dir_result}")
    assert "is a directory" in dir_result
    print("Directory path handled safely.")

    # ---------------------------------------------------------
    # 5. Corrupt PDF handling
    # ---------------------------------------------------------
    print("\n6. Testing corrupt PDF handling...")
    corrupt_result = tool.execute(file_path=corrupt_pdf_path)
    print(f"Result: {corrupt_result}")
    assert "Invalid or corrupt PDF" in corrupt_result or "Error" in corrupt_result
    print("Corrupt PDF handled safely without crashing.")

    # ---------------------------------------------------------
    # 6. Empty / No extractable text handling
    # ---------------------------------------------------------
    print("\n7. Testing PDF with no extractable text...")
    empty_result = tool.execute(file_path=empty_pdf_path)
    print(f"Result: {empty_result}")
    assert "Warning: No extractable text" in empty_result or "scanned" in empty_result
    print("Empty PDF handled safely.")

    # ---------------------------------------------------------
    # 7. Schema and Argument Validation Tests
    # ---------------------------------------------------------
    print("\n8. Testing PDFReaderTool schema and argument validation...")
    assert "file_path" in tool.parameters
    assert tool.parameters["file_path"]["required"] is True

    executor = Executor(tool_registry=registry)

    # Reject placeholder 'parameter_name'
    bad_param_res = executor.execute_action(ToolAction(tool="pdf_reader", arguments={"parameter_name": "file_path"}))
    assert bad_param_res["status"] == "error"
    assert "Invalid placeholder argument 'parameter_name'" in bad_param_res["error"]
    print("Placeholder 'parameter_name' rejected safely by Executor.")

    # Reject missing required arguments
    missing_arg_res = executor.execute_action(ToolAction(tool="pdf_reader", arguments={}))
    assert missing_arg_res["status"] == "error"
    assert "Missing required parameter 'file_path'" in missing_arg_res["error"]
    print("Missing required argument rejected safely by Executor.")

    # ---------------------------------------------------------
    # 8. Execution through Executor via ToolAction
    # ---------------------------------------------------------
    print("\n9. Testing execution through Executor...")
    action = ToolAction(tool="pdf_reader", arguments={"file_path": valid_pdf_path})
    exec_result = executor.execute_action(action)
    print(f"Executor result: {exec_result}")
    assert exec_result["status"] == "completed"
    assert "SOAR Industrial Safety Report" in exec_result["result"]
    print("Executor execution verified.")

    # ---------------------------------------------------------
    # 9. Deterministic Agent Loop Integration Test
    # ---------------------------------------------------------
    print("\n10. Testing Agent Loop with PDFReaderTool...")

    class PDFSequenceResponder:
        def __init__(self, pdf_file: str):
            self.count = 0
            self.pdf_file = pdf_file

        def __call__(self, prompt: str) -> str:
            self.count += 1
            if self.count == 1:
                return json.dumps({
                    "status": "continue",
                    "thought": "I will read the inspection report from the PDF.",
                    "steps": [
                        {
                            "tool": "pdf_reader",
                            "arguments": {"file_path": self.pdf_file}
                        }
                    ]
                })
            else:
                return json.dumps({
                    "status": "complete",
                    "thought": "PDF content has been extracted and reviewed. Task complete.",
                    "steps": []
                })

    mock_responder = PDFSequenceResponder(valid_pdf_path)
    mock_model = MockModel(
        model_id="mock-pdf-agent",
        capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
        priority=1,
        response_fn=mock_responder,
    )

    model_registry = ModelRegistry()
    model_registry.register(mock_model)
    model_router = ModelRouter(model_registry, default_model_id="mock-pdf-agent")
    model_manager = ModelManager(model_registry=model_registry, model_router=model_router)

    planner = Planner(model_manager=model_manager, tool_registry=registry)
    agent = Agent(planner=planner, executor=executor, max_iterations=5)

    agent_state = agent.run(f"Extract information from '{valid_pdf_path}'")

    print(f"Agent Final Status: {agent_state.status}")
    print(f"Agent Iterations: {agent_state.iterations}")
    print(f"Agent Observations: {agent_state.observations}")

    assert agent_state.status == "completed"
    assert agent_state.iterations == 2
    assert len(agent_state.observations) == 1
    assert agent_state.observations[0]["tool"] == "pdf_reader"
    assert "SOAR Industrial Safety Report" in agent_state.observations[0]["result"]
    print("Agent PDF integration test verified successfully!")

finally:
    for p in [valid_pdf_path, empty_pdf_path, corrupt_pdf_path]:
        if os.path.exists(p):
            os.remove(p)
            print(f"Cleaned up test file: {p}")

print("\n[TEST] All PDFReaderTool tests completed successfully!")
