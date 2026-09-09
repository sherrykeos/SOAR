import json
import os
import tempfile
import unittest

from app.models.adapter import ModelCapability
from app.models.manager import ModelManager
from app.models.mock import MockModel
from app.models.registry import ModelRegistry
from app.orchestrator.orchestrator import Orchestrator


class TestOrchestrator(unittest.TestCase):

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".txt")
        self.temp_path = self.temp_file.name.replace("\\", "/")
        self.temp_file.write("Industrial Safety Inspection Report: PASSED")
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_path):
            os.remove(self.temp_path)

    def test_orchestrator_run_with_mock(self):
        class SequenceResponder:
            def __init__(self, file_path: str):
                self.count = 0
                self.file_path = file_path

            def __call__(self, prompt: str) -> str:
                self.count += 1
                if self.count == 1:
                    return json.dumps({
                        "status": "continue",
                        "thought": "Read inspection report",
                        "steps": [{"tool": "read_file", "arguments": {"file_path": self.file_path}}]
                    })
                return json.dumps({
                    "status": "complete",
                    "thought": "Finished reading report",
                    "steps": []
                })

        model_reg = ModelRegistry()
        mock_model = MockModel(
            model_id="qwen3:1.7b",
            capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
            response_fn=SequenceResponder(self.temp_path),
        )
        model_reg.register(mock_model)
        manager = ModelManager(model_registry=model_reg, default_model_name="qwen3:1.7b")

        orchestrator = Orchestrator(model_manager=manager)
        result = orchestrator.run(f"Read the inspection report from '{self.temp_path}'")

        self.assertEqual(result.status, "completed")
        self.assertGreater(len(result.results), 0)
        self.assertEqual(result.results[0]["status"], "completed")
        self.assertIn("Industrial Safety Inspection Report", result.observations[0]["result"])
        self.assertGreater(len(result.events), 0)


if __name__ == "__main__":
    unittest.main()