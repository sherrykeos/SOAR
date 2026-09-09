import io
import shutil
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.app import create_app
from app.api.dependencies import (
    reset_api_dependencies,
    set_api_dependencies,
)
from app.config import (
    ModelDefinitionConfig,
    SOARConfig,
    reset_config,
)
from app.database.repository import DatabaseManager
from app.models.adapter import ModelCapability
from app.models.manager import ModelManager
from app.models.mock import MockModel
from app.models.registry import ModelRegistry
from app.models.router import ModelRouter
from app.orchestrator.events import ProgressEventEmitter
from app.orchestrator.orchestrator import Orchestrator
from app.storage.local import LocalFileStorage


class TestBackendAPI(unittest.TestCase):
    """
    Comprehensive test suite for the SOAR FastAPI Backend REST API.
    Tests health, task execution, event timelines, file upload/download,
    model metadata, and error handling.
    """

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage_dir = Path(self.test_dir) / "files"
        self.db_path = Path(self.test_dir) / "test_api.db"

        # Build test configuration
        self.config = SOARConfig(
            storage={"root": str(self.storage_dir), "max_file_size_bytes": 1024 * 1024},
            database={"path": str(self.db_path)},
            models=[
                ModelDefinitionConfig(
                    id="qwen3:1.7b",
                    provider="mock",
                    capabilities=["general", "reasoning"],
                    priority=10,
                    enabled=True,
                    options={"fixed_response": "Mock general response from qwen3:1.7b."},
                ),
                ModelDefinitionConfig(
                    id="qwen2.5-coder:1.5b",
                    provider="mock",
                    capabilities=["coding"],
                    priority=15,
                    enabled=True,
                    options={"fixed_response": "```python\ndef add(a, b):\n    return a + b\n```"},
                ),
            ],
        )

        # Wire mock model pool
        self.registry = ModelRegistry()
        self.registry.register(
            MockModel(
                model_id="qwen3:1.7b",
                capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
                priority=10,
                fixed_response="Mock general response from qwen3:1.7b.",
            )
        )
        self.registry.register(
            MockModel(
                model_id="qwen2.5-coder:1.5b",
                capabilities={ModelCapability.CODING},
                priority=15,
                fixed_response="```python\ndef add(a, b):\n    return a + b\n```",
            )
        )

        self.router = ModelRouter(self.registry, default_model_id="qwen3:1.7b")
        self.model_manager = ModelManager(
            model_registry=self.registry,
            model_router=self.router,
            default_model_name="qwen3:1.7b",
            config=self.config,
        )

        self.db_manager = DatabaseManager(db_path=self.db_path)
        self.storage = LocalFileStorage(
            storage_dir=self.storage_dir,
            max_file_size_bytes=1024 * 1024,
            db_manager=self.db_manager,
        )
        self.emitter = ProgressEventEmitter()
        self.orchestrator = Orchestrator(
            model_manager=self.model_manager,
            emitter=self.emitter,
            config=self.config,
        )

        # Inject test dependencies
        set_api_dependencies(
            config=self.config,
            db_manager=self.db_manager,
            storage=self.storage,
            emitter=self.emitter,
            model_manager=self.model_manager,
            orchestrator=self.orchestrator,
        )

        self.app = create_app(config=self.config)
        self.client = TestClient(self.app)

    def tearDown(self):
        reset_api_dependencies()
        reset_config()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # -------------------------------------------------------------
    # 1. Health Endpoints
    # -------------------------------------------------------------
    def test_api_health(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["app"], "SOAR")
        self.assertEqual(data["version"], "0.1.0")

    def test_legacy_health(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")

    # -------------------------------------------------------------
    # 2. Task Execution & Event Correlation
    # -------------------------------------------------------------
    def test_create_task_general_direct_answer(self):
        payload = {"task": "What is the primary function of a thermal valve?"}
        resp = self.client.post("/api/tasks", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertTrue(data["run_id"])
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["execution_mode"], "direct_answer")
        self.assertEqual(data["model"], "qwen3:1.7b")
        self.assertIn("Mock general response", data["answer"])
        self.assertGreater(len(data["events"]), 0)

        # Verify event correlation with GET /api/tasks/{run_id}/events
        run_id = data["run_id"]
        events_resp = self.client.get(f"/api/tasks/{run_id}/events")
        self.assertEqual(events_resp.status_code, 200)
        events_data = events_resp.json()
        self.assertEqual(events_data["run_id"], run_id)
        self.assertGreaterEqual(len(events_data["events"]), 2)

        stages = [e["stage"] for e in events_data["events"]]
        self.assertIn("CLASSIFYING", stages)
        self.assertIn("COMPLETED", stages)

    def test_create_task_coding_path(self):
        payload = {"task": "Write a python function to add two numbers."}
        resp = self.client.post("/api/tasks", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["execution_mode"], "code")
        self.assertEqual(data["model"], "qwen2.5-coder:1.5b")
        self.assertIn("def add", data["answer"])

    def test_create_task_empty_prompt_rejected(self):
        payload = {"task": "   "}
        resp = self.client.post("/api/tasks", json=payload)
        self.assertIn(resp.status_code, [400, 422])

    def test_get_events_unknown_run_id_returns_404(self):
        resp = self.client.get("/api/tasks/non-existent-uuid-9999/events")
        self.assertEqual(resp.status_code, 404)

    # -------------------------------------------------------------
    # 3. File Management Endpoints (Upload, Metadata, Download, Delete)
    # -------------------------------------------------------------
    def test_file_lifecycle_upload_download_delete(self):
        # 1. Upload
        file_content = b"%PDF-1.4 SOAR API upload test content."
        upload_resp = self.client.post(
            "/api/files/upload",
            files={"file": ("test_report.pdf", file_content, "application/pdf")},
        )
        self.assertEqual(upload_resp.status_code, 201)
        meta = upload_resp.json()
        file_id = meta["file_id"]
        self.assertEqual(meta["original_filename"], "test_report.pdf")
        self.assertEqual(meta["size_bytes"], len(file_content))
        self.assertEqual(meta["mime_type"], "application/pdf")

        # 2. Get Metadata
        meta_resp = self.client.get(f"/api/files/{file_id}")
        self.assertEqual(meta_resp.status_code, 200)
        self.assertEqual(meta_resp.json()["file_id"], file_id)

        # 3. List Files
        list_resp = self.client.get("/api/files")
        self.assertEqual(list_resp.status_code, 200)
        list_data = list_resp.json()
        self.assertEqual(list_data["total"], 1)
        self.assertEqual(list_data["files"][0]["file_id"], file_id)

        # 4. Download
        download_resp = self.client.get(f"/api/files/{file_id}/download")
        self.assertEqual(download_resp.status_code, 200)
        self.assertEqual(download_resp.content, file_content)

        # 5. Delete
        delete_resp = self.client.delete(f"/api/files/{file_id}")
        self.assertEqual(delete_resp.status_code, 200)
        self.assertEqual(delete_resp.json()["status"], "deleted")

        # 6. Verify subsequent lookup returns 404
        after_resp = self.client.get(f"/api/files/{file_id}")
        self.assertEqual(after_resp.status_code, 404)

    def test_file_upload_traversal_filename_sanitized(self):
        file_content = b"Traversal test"
        upload_resp = self.client.post(
            "/api/files/upload",
            files={"file": ("../../secret_traversal.txt", file_content, "text/plain")},
        )
        self.assertEqual(upload_resp.status_code, 201)
        meta = upload_resp.json()
        self.assertEqual(meta["original_filename"], "secret_traversal.txt")

    def test_file_download_nonexistent_returns_404(self):
        resp = self.client.get("/api/files/non-existent-uuid/download")
        self.assertEqual(resp.status_code, 404)

    # -------------------------------------------------------------
    # 4. Models Endpoint
    # -------------------------------------------------------------
    def test_get_models_list(self):
        resp = self.client.get("/api/models")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["default_model"], "qwen3:1.7b")
        self.assertEqual(len(data["models"]), 2)

        model_ids = [m["id"] for m in data["models"]]
        self.assertIn("qwen3:1.7b", model_ids)
        self.assertIn("qwen2.5-coder:1.5b", model_ids)


if __name__ == "__main__":
    unittest.main()
