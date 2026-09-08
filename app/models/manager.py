from typing import Any

from .adapter import ModelAdapter, ModelCapability
from .mock import MockModel
from .ollama import OllamaModel
from .registry import ModelRegistry
from .router import ModelRouter


class ModelManager:
    """
    Facade managing ModelRegistry and ModelRouter for SOAR on-premise execution.
    Provides plug-and-play local model routing and backward compatibility.
    """

    def __init__(
        self,
        model_registry: ModelRegistry | None = None,
        model_router: ModelRouter | None = None,
        default_model_name: str = "qwen3:1.7b",
    ):
        if model_registry is None:
            self.registry = ModelRegistry()
            self._register_default_models(default_model_name)
        else:
            self.registry = model_registry

        self.router = model_router or ModelRouter(
            registry=self.registry,
            default_model_id=default_model_name,
        )
        self.default_model_name = default_model_name

    def _register_default_models(self, default_model_name: str) -> None:
        # 1. Primary local Ollama model
        ollama_model = OllamaModel(
            model_name=default_model_name,
            capabilities={
                ModelCapability.GENERAL,
                ModelCapability.REASONING,
            },
            priority=10,
        )
        self.registry.register(ollama_model)

        # 2. Secondary Mock model for specialized coding capability testing
        mock_coder = MockModel(
            model_id="mock-coder",
            capabilities={
                ModelCapability.CODING,
            },
            priority=20,
            fixed_response="def solution():\n    return 'SOAR local coding response'",
        )
        self.registry.register(mock_coder)

    @property
    def model(self) -> ModelAdapter:
        """Backwards compatibility property returning the default general model."""
        return self.router.route(task_type=ModelCapability.GENERAL)

    def generate(
        self,
        prompt: str,
        *,
        task_type: str = ModelCapability.GENERAL,
        model_id: str | None = None,
        think: bool = False,
        **kwargs: Any,
    ) -> str:
        """
        Routes the prompt to the appropriate model based on task_type or explicit model_id.
        """
        if model_id is not None:
            model = self.router.route_by_id(model_id)
        else:
            model = self.router.route(task_type=task_type)

        return model.generate(
            prompt,
            think=think,
            **kwargs,
        )