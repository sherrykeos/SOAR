from app.models.manager import ModelManager
from app.orchestrator.planner import Planner
from app.orchestrator.state import AgentState
from app.tools.docx_creator import DOCXCreatorTool
from app.tools.pdf_creator import PDFCreatorTool
from app.tools.pdf_reader import PDFReaderTool
from app.tools.python_sandbox import PythonSandboxTool
from app.tools.read_file import ReadFileTool
from app.tools.registry import ToolRegistry


if __name__ == "__main__":
    print("[TEST] Starting Planner test...", flush=True)

    registry = ToolRegistry()
    registry.register(ReadFileTool())
    registry.register(PDFReaderTool())
    registry.register(DOCXCreatorTool())
    registry.register(PDFCreatorTool())
    registry.register(PythonSandboxTool())

    print("[TEST] Registered 5 default tools in ToolRegistry.", flush=True)

    model_manager = ModelManager()
    planner = Planner(model_manager=model_manager, tool_registry=registry)

    print("\n1. Testing dynamic tool manifest generation in Planner...")
    manifest = planner._format_tools_description()
    print(f"Generated Manifest:\n{manifest}\n")

    # Verify real parameter names are present in manifest
    assert "Tool: pdf_reader" in manifest
    assert "file_path" in manifest
    assert "Tool: docx_creator" in manifest
    assert "output_path" in manifest
    assert "title" in manifest
    assert "content" in manifest
    assert "Tool: python_sandbox" in manifest
    assert "code" in manifest
    print("Planner manifest successfully verified with explicit parameter names.")

    print("\n2. Testing Planner plan generation with registered tools...")
    state = AgentState(
        task="Read the local inspection report file located at 'inspection_report.txt'"
    )

    result = planner.create_plan(state)
    print("\n===== FINAL STATE =====")
    print(f"Status: {result.status}")
    print(f"Plan: {result.plan}")
    print(f"Results: {result.results}")

    assert result.status in ("planned", "completed")
    print("\n[TEST] Planner tests completed successfully!")