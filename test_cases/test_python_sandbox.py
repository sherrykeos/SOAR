import json
import os
import shutil
import tempfile
import time
from pathlib import Path

from app.models.adapter import ModelCapability
from app.models.manager import ModelManager
from app.models.mock import MockModel
from app.models.registry import ModelRegistry
from app.models.router import ModelRouter
from app.orchestrator.action import ToolAction
from app.orchestrator.agent import Agent
from app.orchestrator.executor import Executor
from app.orchestrator.planner import Planner
from app.tools.python_sandbox import PythonSandboxTool
from app.tools.registry import ToolRegistry


print("[TEST] Starting PythonSandboxTool test suite...\n")

# Use a dedicated temporary test sandbox folder to keep workspace clean
test_sandbox_root = tempfile.mkdtemp(prefix="soar_sandbox_test_")

try:
    # Initialize tool with test sandbox directory
    sandbox_tool = PythonSandboxTool(base_sandbox_dir=test_sandbox_root, default_timeout=5)

    # -------------------------------------------------------------
    # 1. Basic Execution: print(2 + 2) -> 4
    # -------------------------------------------------------------
    print("1. Testing Basic Execution (2 + 2)...")
    res1 = sandbox_tool.execute(code="print(2 + 2)")
    print(f"Result 1:\n{res1}\n")
    assert "Status: Success" in res1
    assert "4" in res1
    print("Basic execution test passed.")

    # -------------------------------------------------------------
    # 2. Multiple Statements
    # -------------------------------------------------------------
    print("\n2. Testing Multiple Statements...")
    multi_code = (
        "x = 10\n"
        "y = 20\n"
        "z = x * y\n"
        "print(f'Calculated Product: {z}')"
    )
    res2 = sandbox_tool.execute(code=multi_code)
    print(f"Result 2:\n{res2}\n")
    assert "Status: Success" in res2
    assert "Calculated Product: 200" in res2
    print("Multiple statements test passed.")

    # -------------------------------------------------------------
    # 3. Stdout Capture
    # -------------------------------------------------------------
    print("\n3. Testing Stdout Capture across multiple prints...")
    stdout_code = (
        "for i in range(3):\n"
        "    print(f'Line {i+1}')"
    )
    res3 = sandbox_tool.execute(code=stdout_code)
    print(f"Result 3:\n{res3}\n")
    assert "Line 1" in res3
    assert "Line 2" in res3
    assert "Line 3" in res3
    print("Stdout capture test passed.")

    # -------------------------------------------------------------
    # 4. Python Exception Handling
    # -------------------------------------------------------------
    print("\n4. Testing Python Exception Handling (ZeroDivisionError)...")
    error_code = (
        "a = 10\n"
        "b = 0\n"
        "print(a / b)"
    )
    res4 = sandbox_tool.execute(code=error_code)
    print(f"Result 4:\n{res4}\n")
    assert "Status: Failed" in res4
    assert "ZeroDivisionError" in res4
    print("Exception handling test passed.")

    # -------------------------------------------------------------
    # 5. Timeout Handling
    # -------------------------------------------------------------
    print("\n5. Testing Timeout Handling...")
    timeout_code = (
        "import time\n"
        "time.sleep(5)\n"
        "print('Done sleeping')"
    )
    res5 = sandbox_tool.execute(code=timeout_code, timeout=1)
    print(f"Result 5:\n{res5}\n")
    assert "timed out after 1 seconds" in res5
    print("Timeout handling test passed.")

    # -------------------------------------------------------------
    # 6 & 7. File Creation Inside Sandbox Workspace & Verification
    # -------------------------------------------------------------
    print("\n6 & 7. Testing File Creation inside Sandbox Workspace...")
    file_create_code = (
        "with open('report_data.csv', 'w') as f:\n"
        "    f.write('id,sensor,val\\n1,pressure,14.5\\n2,temperature,78.2\\n')\n"
        "print('CSV generated successfully.')"
    )
    res6 = sandbox_tool.execute(code=file_create_code)
    print(f"Result 6:\n{res6}\n")
    assert "Status: Success" in res6
    assert "Workspace files created: report_data.csv" in res6

    created_csv_path = Path(test_sandbox_root) / "workspace" / "report_data.csv"
    assert created_csv_path.exists(), "Workspace file was not created on disk!"
    csv_content = created_csv_path.read_text()
    assert "pressure,14.5" in csv_content
    print(f"Verified created file exists on disk with content:\n{csv_content}")

    # -------------------------------------------------------------
    # 8. Attempted Path Traversal Rejection
    # -------------------------------------------------------------
    print("\n8. Testing Attempted Path Traversal Rejection...")
    traversal_code = "with open('../secret.txt', 'w') as f: f.write('hacked')"
    res8 = sandbox_tool.execute(code=traversal_code)
    print(f"Result 8:\n{res8}\n")
    assert "Security violation" in res8
    assert "Path traversal escape sequence" in res8
    print("Path traversal attempt successfully blocked.")

    # -------------------------------------------------------------
    # 9. Attempted Access Outside Sandbox (Disallowed Modules)
    # -------------------------------------------------------------
    print("\n9. Testing Disallowed Module / Network Import Rejection...")
    net_code = (
        "import socket\n"
        "s = socket.socket()\n"
        "print('Connected')"
    )
    res9 = sandbox_tool.execute(code=net_code)
    print(f"Result 9:\n{res9}\n")
    assert "Security violation" in res9
    assert "socket" in res9
    print("Disallowed network module successfully blocked.")

    # -------------------------------------------------------------
    # 10. Executor Tool Invocation
    # -------------------------------------------------------------
    print("\n10. Testing Execution through Executor...")
    registry = ToolRegistry()
    registry.register(sandbox_tool)

    executor = Executor(tool_registry=registry)
    action = ToolAction(
        tool="python_sandbox",
        arguments={
            "code": "nums = [1, 2, 3, 4, 5]\nprint(f'Sum: {sum(nums)}')"
        },
    )
    exec_res = executor.execute_action(action)
    print(f"Executor result:\n{exec_res}\n")
    assert exec_res["status"] == "completed"
    assert "Sum: 15" in exec_res["result"]
    print("Executor execution verified successfully.")

    # -------------------------------------------------------------
    # 11. Deterministic Agent-level Test with Python Sandbox
    # -------------------------------------------------------------
    print("\n11. Testing Agent Loop Integration with python_sandbox...")

    class SandboxSequenceResponder:
        def __init__(self):
            self.count = 0

        def __call__(self, prompt: str) -> str:
            self.count += 1
            if self.count == 1:
                return json.dumps({
                    "status": "continue",
                    "thought": "I need to calculate the average temperature from data using python_sandbox.",
                    "steps": [
                        {
                            "tool": "python_sandbox",
                            "arguments": {
                                "code": "temps = [72.5, 75.0, 78.5, 71.0]\navg = sum(temps) / len(temps)\nprint(f'Average Temp: {avg:.2f}')"
                            }
                        }
                    ]
                })
            else:
                return json.dumps({
                    "status": "complete",
                    "thought": "Calculation finished and verified. Task complete.",
                    "steps": []
                })

    mock_model = MockModel(
        model_id="mock-sandbox-agent",
        capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
        priority=1,
        response_fn=SandboxSequenceResponder(),
    )

    model_registry = ModelRegistry()
    model_registry.register(mock_model)
    model_router = ModelRouter(model_registry, default_model_id="mock-sandbox-agent")
    model_manager = ModelManager(model_registry=model_registry, model_router=model_router)

    planner = Planner(model_manager=model_manager, tool_registry=registry)
    agent = Agent(planner=planner, executor=executor, max_iterations=5)

    agent_state = agent.run("Calculate average temperature from sensor readings.")
    print(f"Agent Final Status: {agent_state.status}")
    print(f"Agent Iterations: {agent_state.iterations}")
    print(f"Agent Observations: {agent_state.observations}")

    assert agent_state.status == "completed"
    assert agent_state.iterations == 2
    assert len(agent_state.observations) == 1
    assert agent_state.observations[0]["tool"] == "python_sandbox"
    assert "Average Temp: 74.25" in agent_state.observations[0]["result"]
    print("Agent python_sandbox integration verified successfully!")

finally:
    if os.path.exists(test_sandbox_root):
        shutil.rmtree(test_sandbox_root, ignore_errors=True)
        print(f"\nCleaned up test sandbox directory: {test_sandbox_root}")

print("\n[TEST] All PythonSandboxTool tests passed successfully!")
