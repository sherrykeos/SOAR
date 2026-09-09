import os
import shutil
import tempfile
import unittest
from pathlib import Path

from app.config import (
    AppConfig,
    ConfigError,
    ConfigFileNotFoundError,
    ConfigParsingError,
    ConfigValidationError,
    ModelDefinitionConfig,
    SOARConfig,
    get_config,
    get_project_root,
    load_config,
    reset_config,
    resolve_project_path,
    set_config,
    validate_config,
)
from app.models.adapter import ModelCapability
from app.models.manager import ModelManager
from app.models.router import ModelRouter
from app.orchestrator.routing import TaskProfile


class TestConfigurationSystem(unittest.TestCase):
    """
    Test suite for the Centralized Application Configuration System.
    Validates loading, schema validation, dynamic model pool configuration,
    router capability matching, and portability.
    """

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        reset_config()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        reset_config()

    # -------------------------------------------------------------
    # 1. Loading & Parsing Tests
    # -------------------------------------------------------------
    def test_load_default_config_file(self):
        config = load_config()
        self.assertIsInstance(config, SOARConfig)
        self.assertEqual(config.app.name, "SOAR")
        self.assertGreater(len(config.models), 0)
        self.assertEqual(config.storage.root, "./data/files")
        self.assertEqual(config.database.path, "./data/soar.db")

    def test_load_custom_valid_yaml(self):
        custom_yaml = """
app:
  name: "SOAR-Cluster"
  environment: "production"
  debug: true

models:
  - id: "custom-general:8b"
    provider: "ollama"
    capabilities:
      - "general"
    priority: 5
    enabled: true

storage:
  root: "./custom_data/files"
  max_file_size_bytes: 10485760

agent:
  max_iterations: 10
  default_model_id: "custom-general:8b"
"""
        yaml_path = Path(self.test_dir) / "custom_config.yaml"
        yaml_path.write_text(custom_yaml, encoding="utf-8")

        config = load_config(yaml_path)
        self.assertEqual(config.app.name, "SOAR-Cluster")
        self.assertEqual(config.app.environment, "production")
        self.assertTrue(config.app.debug)
        self.assertEqual(len(config.models), 1)
        self.assertEqual(config.models[0].id, "custom-general:8b")
        self.assertEqual(config.agent.max_iterations, 10)
        self.assertEqual(config.storage.max_file_size_bytes, 10485760)

    def test_missing_config_file_explicit_path_raises_error(self):
        non_existent = Path(self.test_dir) / "missing_file.yaml"
        with self.assertRaises(ConfigFileNotFoundError):
            load_config(non_existent)

    def test_malformed_yaml_syntax(self):
        bad_yaml = "app:\n  name: [unclosed list"
        yaml_path = Path(self.test_dir) / "bad_syntax.yaml"
        yaml_path.write_text(bad_yaml, encoding="utf-8")

        with self.assertRaises(ConfigParsingError):
            load_config(yaml_path)

    # -------------------------------------------------------------
    # 2. Validation Rule Tests
    # -------------------------------------------------------------
    def test_validation_duplicate_model_id(self):
        config = SOARConfig(
            models=[
                ModelDefinitionConfig(id="model-a", capabilities=["general"]),
                ModelDefinitionConfig(id="model-a", capabilities=["reasoning"]),
            ]
        )
        with self.assertRaises(ConfigValidationError) as ctx:
            validate_config(config)
        self.assertIn("Duplicate model ID", str(ctx.exception))

    def test_validation_invalid_capability(self):
        config = SOARConfig(
            models=[
                ModelDefinitionConfig(id="model-a", capabilities=["invalid_super_magic"]),
            ]
        )
        with self.assertRaises(ConfigValidationError) as ctx:
            validate_config(config)
        self.assertIn("Invalid capability", str(ctx.exception))

    def test_validation_unsupported_provider(self):
        config = SOARConfig(
            models=[
                ModelDefinitionConfig(id="model-a", provider="unsupported_cloud_api"),
            ]
        )
        with self.assertRaises(ConfigValidationError) as ctx:
            validate_config(config)
        self.assertIn("Unsupported provider", str(ctx.exception))

    def test_validation_negative_timeout(self):
        config = SOARConfig(
            models=[
                ModelDefinitionConfig(id="model-a", timeout=-5.0),
            ]
        )
        with self.assertRaises(ConfigValidationError) as ctx:
            validate_config(config)
        self.assertIn("timeout", str(ctx.exception))

    def test_validation_invalid_agent_iterations(self):
        config = SOARConfig()
        config.agent.max_iterations = 0
        with self.assertRaises(ConfigValidationError):
            validate_config(config)

    def test_validation_rag_chunk_overlap_exceeds_chunk_size(self):
        config = SOARConfig()
        config.rag.chunk_size = 100
        config.rag.chunk_overlap = 150
        with self.assertRaises(ConfigValidationError) as ctx:
            validate_config(config)
        self.assertIn("chunk_overlap", str(ctx.exception))

    # -------------------------------------------------------------
    # 3. Dynamic Model Registration & Routing Tests
    # -------------------------------------------------------------
    def test_model_manager_populates_from_config(self):
        custom_config = SOARConfig(
            models=[
                ModelDefinitionConfig(
                    id="my-custom-llm:7b",
                    provider="mock",
                    capabilities=["general", "reasoning"],
                    priority=5,
                    enabled=True,
                    options={"fixed_response": "Custom LLM Response"},
                ),
                ModelDefinitionConfig(
                    id="disabled-llm:13b",
                    provider="mock",
                    capabilities=["coding"],
                    priority=10,
                    enabled=False,
                ),
            ]
        )

        manager = ModelManager(config=custom_config)
        registered_ids = [m.model_id for m in manager.registry.list_models()]

        self.assertIn("my-custom-llm:7b", registered_ids)
        self.assertNotIn("disabled-llm:13b", registered_ids)

        model = manager.registry.get("my-custom-llm:7b")
        self.assertEqual(model.generate("test prompt"), "Custom LLM Response")

    def test_router_selects_dynamically_configured_model(self):
        custom_config = SOARConfig(
            models=[
                ModelDefinitionConfig(
                    id="deepseek-coder:6.7b",
                    provider="mock",
                    capabilities=["coding"],
                    priority=1,
                    enabled=True,
                ),
                ModelDefinitionConfig(
                    id="general-fallback:1.7b",
                    provider="mock",
                    capabilities=["general"],
                    priority=10,
                    enabled=True,
                ),
            ]
        )

        manager = ModelManager(config=custom_config)
        coding_profile = TaskProfile(
            task_type="coding",
            complexity="medium",
            execution_mode="code",
            requires_coding=True,
        )

        decision = manager.router.route_task(coding_profile)
        # Should dynamically pick deepseek-coder:6.7b without any code changes
        self.assertEqual(decision.requested_model_id, "deepseek-coder:6.7b")
        self.assertEqual(decision.selected_model.model_id, "deepseek-coder:6.7b")

    # -------------------------------------------------------------
    # 4. Portability & Path Resolution Tests
    # -------------------------------------------------------------
    def test_project_root_and_path_resolution(self):
        root = get_project_root()
        self.assertTrue(root.exists())
        self.assertTrue((root / "app").is_dir())

        resolved_storage = resolve_project_path("./data/files")
        self.assertTrue(resolved_storage.is_absolute())
        self.assertEqual(resolved_storage, (root / "data/files").resolve())


if __name__ == "__main__":
    unittest.main()
