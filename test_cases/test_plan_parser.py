import json
import os
import tempfile

from app.orchestrator.action import ToolAction
from app.orchestrator.executor import Executor
from app.orchestrator.plan import StructuredPlan
from app.orchestrator.plan_parser import PlanParseError, PlanParser
from app.tools.read_file import ReadFileTool
from app.tools.registry import ToolRegistry


print("[TEST] Starting PlanParser test suite...\n")

# 1. Valid plan parsing
print("1. Testing valid plan parsing...")
valid_plan_json = json.dumps({
    "steps": [
        {
            "tool": "read_file",
            "arguments": {
                "file_path": "sample.txt"
            }
        }
    ]
})
plan = PlanParser.parse(valid_plan_json)
assert isinstance(plan, StructuredPlan)
assert len(plan.steps) == 1
assert isinstance(plan.steps[0], ToolAction)
assert plan.steps[0].tool == "read_file"
assert plan.steps[0].arguments == {"file_path": "sample.txt"}
print(f"Parsed successfully: {plan}")

# 2. Missing 'steps' field
print("\n2. Testing missing 'steps' field...")
missing_steps_json = json.dumps({"plan": []})
try:
    PlanParser.parse(missing_steps_json)
    assert False, "Should have raised PlanParseError"
except PlanParseError as e:
    print(f"Caught expected error: {e}")

# 3. 'steps' field is not a list
print("\n3. Testing 'steps' is not a list...")
invalid_steps_json = json.dumps({"steps": "read_file"})
try:
    PlanParser.parse(invalid_steps_json)
    assert False, "Should have raised PlanParseError"
except PlanParseError as e:
    print(f"Caught expected error: {e}")

# 4. Malformed JSON
print("\n4. Testing malformed JSON...")
malformed_json = '{"steps": [{"tool": "read_file", '
try:
    PlanParser.parse(malformed_json)
    assert False, "Should have raised PlanParseError"
except PlanParseError as e:
    print(f"Caught expected error: {e}")

# 5. Malformed action inside steps
print("\n5. Testing malformed action inside steps...")
malformed_action_json = json.dumps({
    "steps": [
        {"tool": ""}
    ]
})
try:
    PlanParser.parse(malformed_action_json)
    assert False, "Should have raised PlanParseError"
except PlanParseError as e:
    print(f"Caught expected error: {e}")

# 6. Unknown tool validation against ToolRegistry
print("\n6. Testing unknown tool validation against ToolRegistry...")
registry = ToolRegistry()
registry.register(ReadFileTool())

unknown_tool_json = json.dumps({
    "steps": [
        {"tool": "unknown_tool_xyz", "arguments": {}}
    ]
})
unknown_plan = PlanParser.parse(unknown_tool_json)
try:
    PlanParser.validate_tools(unknown_plan, registry)
    assert False, "Should have raised PlanParseError for unknown tool"
except PlanParseError as e:
    print(f"Caught expected error: {e}")

# 7. Markdown fence stripping robustness
print("\n7. Testing markdown fence stripping...")
markdown_fenced_json = """```json
{
  "steps": [
    {
      "tool": "read_file",
      "arguments": {
        "file_path": "report.txt"
      }
    }
  ]
}
```"""
fenced_plan = PlanParser.parse(markdown_fenced_json)
assert len(fenced_plan.steps) == 1
assert fenced_plan.steps[0].tool == "read_file"
print("Markdown fenced JSON parsed cleanly.")

# 8. End-to-end deterministic pipeline with temporary file
print("\n8. Testing End-to-End deterministic pipeline (Plan -> Parser -> Executor -> Tool)...")
with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".txt") as temp_file:
    temp_path = temp_file.name
    temp_file.write("SOAR Sovereign Inspection Report: OK")

try:
    plan_json = json.dumps({
        "steps": [
            {
                "tool": "read_file",
                "arguments": {
                    "file_path": temp_path
                }
            }
        ]
    })

    # 1. Parse plan
    parsed_plan = PlanParser.parse(plan_json)
    # 2. Validate tools
    PlanParser.validate_tools(parsed_plan, registry)
    # 3. Execute via Executor
    executor = Executor(tool_registry=registry)
    result = executor.execute_action(parsed_plan.steps[0])

    print(f"Execution Result: {result}")
    assert result["status"] == "completed"
    assert result["tool"] == "read_file"
    assert result["result"] == "SOAR Sovereign Inspection Report: OK"
    print("End-to-End plan execution verified successfully!")

finally:
    if os.path.exists(temp_path):
        os.remove(temp_path)
        print(f"Cleaned up temporary test file at: {temp_path}")

print("\n[TEST] All PlanParser tests completed successfully!")
