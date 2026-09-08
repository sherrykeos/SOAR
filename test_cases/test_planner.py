from app.models.manager import ModelManager
from app.orchestrator.planner import Planner
from app.orchestrator.state import AgentState


print("[TEST] Starting...", flush=True)

model_manager = ModelManager()

print("[TEST] ModelManager created", flush=True)

planner = Planner(model_manager)

print("[TEST] Planner created", flush=True)

state = AgentState(
    task="Read an inspection report and create an approval note"
)

print("[TEST] State created", flush=True)
print("[TEST] Calling planner...", flush=True)

result = planner.create_plan(state)

print("[TEST] Planner returned", flush=True)

print("\n===== FINAL STATE =====")
print(result)