import os
import tempfile
from pathlib import Path

from app.orchestrator import Orchestrator
from app.orchestrator.agent import AgentState
from app.orchestrator.execution import Executor, ToolAction
from app.tools.base import BaseTool
from app.tools.read_file import ReadFileTool
from app.tools.registry import ToolRegistry


print("[TEST] Starting Executor and ToolAction test suite...\n")

# 1. Test ToolAction representation
print("1. Testing ToolAction representation...")
action = ToolAction(tool="read_file", arguments={"file_path": "sample.txt"})
assert action.tool == "read_file"
assert action.arguments == {"file_path": "sample.txt"}
print(f"ToolAction created successfully: {action}")

# Create a temporary file for filesystem tests
with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".txt") as temp_file:
    temp_path = temp_file.name
    temp_file.write("SOAR Sovereign Agent Data: Confidential")

print(f"\nCreated temporary test file at: {temp_path}")

try:
    # 2 & 3. Test Executor executing ReadFileTool and returning correct contents
    print("\n2 & 3. Testing Executor executing ReadFileTool...")
    registry = ToolRegistry()
    registry.register(ReadFileTool())
    executor = Executor(tool_registry=registry)

    read_action = ToolAction(tool="read_file", arguments={"file_path": temp_path})
    result = executor.execute_action(read_action)

    print(f"Executor result: {result}")
    assert result["status"] == "completed"
    assert result["tool"] == "read_file"
    assert result["result"] == "SOAR Sovereign Agent Data: Confidential"
    print("Executor successfully executed registered tool and returned matching content.")

    # 4. Test unknown tool handling
    print("\n4. Testing unknown tool handling in Executor...")
    unknown_action = ToolAction(tool="non_existent_tool", arguments={})
    unknown_result = executor.execute_action(unknown_action)
    print(f"Unknown tool result: {unknown_result}")
    assert unknown_result["status"] == "error"
    assert "not found" in unknown_result["error"]
    print("Unknown tool handled safely without crashing.")

    # 5. Test tool execution error handling (e.g. failing tool)
    print("\n5. Testing tool exception handling in Executor...")

    class FaultyTool(BaseTool):
        @property
        def name(self) -> str:
            return "faulty_tool"

        @property
        def description(self) -> str:
            return "A tool that raises an unexpected exception."

        def execute(self, **kwargs):
            raise RuntimeError("Simulated internal tool crash")

    registry.register(FaultyTool())
    faulty_action = ToolAction(tool="faulty_tool", arguments={})
    faulty_result = executor.execute_action(faulty_action)
    print(f"Faulty tool result: {faulty_result}")
    assert faulty_result["status"] == "error"
    assert "Simulated internal tool crash" in faulty_result["error"]
    print("Tool exception handled safely by Executor.")

    # 6. Test Orchestrator -> Executor -> ToolRegistry -> ReadFileTool flow
    print("\n6. Testing Orchestrator integration with ToolRegistry and state execution...")
    orchestrator = Orchestrator()
    # Confirm default tool is registered
    registered_tool_names = [t.name for t in orchestrator.tool_registry.list_tools()]
    print(f"Registered tools in Orchestrator: {registered_tool_names}")
    assert "read_file" in registered_tool_names

    # Test executing a state containing a ToolAction
    state = AgentState(
        task="Read secret file",
        plan=[ToolAction(tool="read_file", arguments={"file_path": temp_path})],
    )
    executed_state = orchestrator.executor.execute(state)
    print(f"Executed State status: {executed_state.status}")
    print(f"Executed State results: {executed_state.results}")
    assert executed_state.status == "completed"
    assert executed_state.results[0]["status"] == "completed"
    assert executed_state.results[0]["result"] == "SOAR Sovereign Agent Data: Confidential"
    print("Orchestrator executor pipeline verified successfully.")

finally:
    if os.path.exists(temp_path):
        os.remove(temp_path)
        print(f"\nCleaned up temporary test file at: {temp_path}")

print("\n[TEST] All Executor and ToolAction tests passed successfully!")
