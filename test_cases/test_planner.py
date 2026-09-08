from app.models.manager import ModelManager
from app.orchestrator.planner import Planner
from app.orchestrator.state import AgentState
from app.tools.read_file import ReadFileTool
from app.tools.registry import ToolRegistry


print("[TEST] Starting Planner test...", flush=True)

registry = ToolRegistry()
registry.register(ReadFileTool())

print("[TEST] ToolRegistry created with ReadFileTool", flush=True)

model_manager = ModelManager()
planner = Planner(model_manager=model_manager, tool_registry=registry)

print("[TEST] Planner created", flush=True)

state = AgentState(
    task="Read the local inspection report file located at 'inspection_report.txt'"
)

print("[TEST] Calling planner...", flush=True)
result = planner.create_plan(state)

print("[TEST] Planner returned", flush=True)
print("\n===== FINAL STATE =====")
print(result)