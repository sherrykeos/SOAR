import json
import os
import tempfile

from app.orchestrator.execution import ActionParseError, ActionParser, Executor, ToolAction
from app.tools.read_file import ReadFileTool
from app.tools.registry import ToolRegistry


print("[TEST] Starting ActionParser test suite...\n")

# 1. Valid action with tool and arguments
print("1. Testing valid action parsing...")
valid_json = json.dumps({
    "tool": "read_file",
    "arguments": {
        "file_path": "sample.txt"
    }
})
action = ActionParser.parse(valid_json)
assert isinstance(action, ToolAction)
assert action.tool == "read_file"
assert action.arguments == {"file_path": "sample.txt"}
print(f"Parsed successfully: {action}")

# 2. Valid action with missing/optional arguments
print("\n2. Testing action with missing arguments field...")
no_args_json = json.dumps({
    "tool": "read_file"
})
action_no_args = ActionParser.parse(no_args_json)
assert isinstance(action_no_args, ToolAction)
assert action_no_args.tool == "read_file"
assert action_no_args.arguments == {}
print(f"Parsed successfully: {action_no_args}")

# 3. Missing tool field
print("\n3. Testing missing tool field...")
missing_tool_json = json.dumps({
    "arguments": {"file_path": "sample.txt"}
})
try:
    ActionParser.parse(missing_tool_json)
    assert False, "Should have raised ActionParseError"
except ActionParseError as e:
    print(f"Caught expected error: {e}")

# 4. Invalid JSON
print("\n4. Testing invalid JSON...")
invalid_json = '{"tool": "read_file", "arguments": '
try:
    ActionParser.parse(invalid_json)
    assert False, "Should have raised ActionParseError"
except ActionParseError as e:
    print(f"Caught expected error: {e}")

# 5. Invalid arguments type (string instead of dict)
print("\n5. Testing invalid arguments type...")
invalid_args_json = json.dumps({
    "tool": "read_file",
    "arguments": "sample.txt"
})
try:
    ActionParser.parse(invalid_args_json)
    assert False, "Should have raised ActionParseError"
except ActionParseError as e:
    print(f"Caught expected error: {e}")

# 6. Invalid root type (list instead of dict)
print("\n6. Testing invalid root type (array)...")
invalid_root_json = json.dumps([
    {"tool": "read_file"}
])
try:
    ActionParser.parse(invalid_root_json)
    assert False, "Should have raised ActionParseError"
except ActionParseError as e:
    print(f"Caught expected error: {e}")

# 7. End-to-end: JSON -> ActionParser -> ToolAction -> Executor -> ToolRegistry -> ReadFileTool
print("\n7. Testing End-to-End pipeline (JSON -> Parser -> Executor -> Tool)...")
with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".txt") as temp_file:
    temp_path = temp_file.name
    temp_file.write("SOAR Protocol Verification: Passed")

try:
    registry = ToolRegistry()
    registry.register(ReadFileTool())
    executor = Executor(tool_registry=registry)

    structured_json_call = json.dumps({
        "tool": "read_file",
        "arguments": {
            "file_path": temp_path
        }
    })

    # Parse JSON into ToolAction
    parsed_action = ActionParser.parse(structured_json_call)
    print(f"Parsed Action: {parsed_action}")

    # Execute ToolAction via Executor
    exec_result = executor.execute_action(parsed_action)
    print(f"Execution Result: {exec_result}")

    assert exec_result["status"] == "completed"
    assert exec_result["tool"] == "read_file"
    assert exec_result["result"] == "SOAR Protocol Verification: Passed"
    print("End-to-End parser and executor pipeline successfully verified!")

finally:
    if os.path.exists(temp_path):
        os.remove(temp_path)
        print(f"Cleaned up temporary test file at: {temp_path}")

print("\n[TEST] All ActionParser tests completed successfully!")
