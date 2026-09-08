from .adapter import ModelAdapter, ModelCapability
from .registry import ModelRegistry


class ModelRouter:

    def __init__(
        self,
        registry: ModelRegistry,
        default_model_id: str | None = None,
    ):
        self.registry = registry
        self.default_model_id = default_model_id

    def route(self, task_type: str = ModelCapability.GENERAL) -> ModelAdapter:
        """
        Selects the best available model for the given task_type / capability.
        Raises ValueError if no registered model supports the capability.
        """
        candidates = self.registry.find_by_capability(task_type)
        if candidates:
            return candidates[0]

        raise ValueError(
            f"No registered model supports capability '{task_type}'. "
            f"Available models: {[m.model_id for m in self.registry.list_models()]}"
        )

    def route_by_id(self, model_id: str) -> ModelAdapter:
        """Retrieves a specific model by model_id."""
        return self.registry.get(model_id)
