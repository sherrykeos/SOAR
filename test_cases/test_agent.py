import json
import os
import tempfile

from app.models.adapter import ModelCapability
from app.models.manager import ModelManager
from app.models.mock import MockModel
from app.models.registry import ModelRegistry
from app.models.router import ModelRouter
from app.orchestrator.agent import Agent
from app.orchestrator.executor import Executor
from app.orchestrator.planner import Planner
from app.tools.base import BaseTool
from app.tools.read_file import ReadFileTool
from app.tools.registry import ToolRegistry


print("[TEST] Starting Agent Loop test suite...\n")

# Create a temporary file for deterministic testing
with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".txt") as temp_file:
    temp_path = temp_file.name.replace("\\", "/")
    temp_file.write("SOAR Inspection Report: ALL SYSTEMS OPERATIONAL")

print(f"Temporary test file created at: {temp_path}")

try:
    # -------------------------------------------------------------
    # 1. Deterministic Multi-Turn Loop (Plan -> Act -> Observe -> Complete)
    # -------------------------------------------------------------
    print("\n1. Testing Deterministic Multi-Turn Agent Loop...")

    class SequenceResponder:
        def __init__(self, file_path: str):
            self.count = 0
            self.file_path = file_path

        def __call__(self, prompt: str) -> str:
            self.count += 1
            if self.count == 1:
                # Iteration 1: Plan to read file
                return json.dumps({
                    "status": "continue",
                    "thought": "I need to read the inspection file first.",
                    "steps": [
                        {
                            "tool": "read_file",
                            "arguments": {"file_path": self.file_path}
                        }
                    ]
                })
            else:
                # Iteration 2: After seeing file content in observations, complete task
                return json.dumps({
                    "status": "complete",
                    "thought": "Inspection file has been read and verified. Task complete.",
                    "steps": []
                })

    mock_responder = SequenceResponder(temp_path)
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

    print(f"\nFinal State Status: {final_state.status}")
    print(f"Total Iterations: {final_state.iterations}")
    print(f"Observations Recorded: {len(final_state.observations)}")
    print(f"Results: {final_state.results}")

    assert final_state.status == "completed"
    assert final_state.iterations == 2
    assert len(final_state.observations) == 1
    assert final_state.observations[0]["tool"] == "read_file"
    assert final_state.observations[0]["result"] == "SOAR Inspection Report: ALL SYSTEMS OPERATIONAL"
    print("Deterministic Multi-Turn loop successfully verified!")

    # -------------------------------------------------------------
    # 2. Safety Test: Unknown Tool Rejection
    # -------------------------------------------------------------
    print("\n2. Testing Unknown Tool Rejection...")
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
    evil_planner = Planner(model_manager=evil_mgr, tool_registry=tool_registry)
    evil_agent = Agent(planner=evil_planner, executor=executor, max_iterations=3)

    evil_state = evil_agent.run("Do something malicious.")
    print(f"Unknown Tool State Status: {evil_state.status}")
    assert evil_state.status == "error"
    assert "Unknown tool 'evil_tool'" in evil_state.results[0]["error"]
    print("Unknown tool rejected safely before execution.")

    # -------------------------------------------------------------
    # 3. Safety Test: Malformed Plan (Invalid JSON)
    # -------------------------------------------------------------
    print("\n3. Testing Malformed Plan Handling...")
    broken_mock = MockModel(
        model_id="broken-mock",
        capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
        fixed_response="I cannot output JSON today!",
    )
    broken_registry = ModelRegistry()
    broken_registry.register(broken_mock)
    broken_mgr = ModelManager(model_registry=broken_registry, model_router=ModelRouter(broken_registry))
    broken_planner = Planner(model_manager=broken_mgr, tool_registry=tool_registry)
    broken_agent = Agent(planner=broken_planner, executor=executor, max_iterations=3)

    broken_state = broken_agent.run("Test invalid JSON.")
    print(f"Broken Plan State Status: {broken_state.status}")
    assert broken_state.status == "error"
    assert "Plan parsing/validation failed" in broken_state.results[0]["error"]
    print("Malformed plan handled safely in controlled error state.")

    # -------------------------------------------------------------
    # 4. Safety Test: Infinite-Loop Protection (Max Iterations)
    # -------------------------------------------------------------
    print("\n4. Testing Infinite-Loop Protection (Max Iterations)...")
    infinite_mock = MockModel(
        model_id="infinite-mock",
        capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
        fixed_response=json.dumps({
            "status": "continue",
            "steps": [{"tool": "read_file", "arguments": {"file_path": temp_path}}]
        })
    )
    inf_registry = ModelRegistry()
    inf_registry.register(infinite_mock)
    inf_mgr = ModelManager(model_registry=inf_registry, model_router=ModelRouter(inf_registry))
    inf_planner = Planner(model_manager=inf_mgr, tool_registry=tool_registry)
    inf_agent = Agent(planner=inf_planner, executor=executor, max_iterations=3)

    inf_state = inf_agent.run("Loop forever.")
    print(f"Infinite State Status: {inf_state.status}, Iterations: {inf_state.iterations}")
    assert inf_state.status == "max_iterations_reached"
    assert inf_state.iterations == 3
    print("Infinite-loop prevented safely at max_iterations.")

    # -------------------------------------------------------------
    # 5. Safety Test: Tool Runtime Failure Handling
    # -------------------------------------------------------------
    print("\n5. Testing Tool Runtime Failure Handling...")

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
    print(f"Crash State Observations: {crash_state.observations}")
    assert len(crash_state.observations) > 0
    assert crash_state.observations[0]["status"] == "error"
    assert "Database connection lost" in crash_state.observations[0]["result"]
    print("Tool crash contained safely and recorded in observations.")

finally:
    if os.path.exists(temp_path):
        os.remove(temp_path)
        print(f"\nCleaned up test file at: {temp_path}")

print("\n[TEST] All Agent Loop tests passed successfully!")
