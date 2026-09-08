import os
import tempfile

from app.orchestrator.orchestrator import Orchestrator

# Create a sample inspection report file
with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".txt") as temp_file:
    temp_path = temp_file.name
    temp_file.write("Industrial Safety Inspection Report: PASSED")

try:
    orchestrator = Orchestrator()

    normalized_path = temp_path.replace("\\", "/")
    result = orchestrator.run(
        f"Read the inspection report from '{normalized_path}'"
    )

    print("\n===== ORCHESTRATOR EXECUTION RESULT =====")
    print(f"Task: {result.task}")
    print(f"Status: {result.status}")
    print(f"Plan: {result.plan}")
    print(f"Results: {result.results}")

    assert result.status in ("completed", "max_iterations_reached")
    assert len(result.results) > 0
    assert result.results[0]["status"] == "completed"
finally:
    if os.path.exists(temp_path):
        os.remove(temp_path)