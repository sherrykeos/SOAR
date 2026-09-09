from typing import List

from .adapter import ModelAdapter


class ModelRegistry:

    def __init__(self):
        self._models: dict[str, ModelAdapter] = {}

    def register(self, model: ModelAdapter) -> None:
        if model.model_id in self._models:
            raise ValueError(
                f"Model already registered: {model.model_id}"
            )
        self._models[model.model_id] = model

    def get(self, model_id: str) -> ModelAdapter:
        if model_id not in self._models:
            raise KeyError(
                f"Model not found: {model_id}"
            )
        return self._models[model_id]

    def list_models(self) -> List[ModelAdapter]:
        return list(self._models.values())

    def find_by_capability(self, capability: str) -> List[ModelAdapter]:
        """Returns matching models sorted by priority (lowest integer = highest priority)."""
        matching = [
            m for m in self._models.values()
            if capability in m.capabilities
        ]
        return sorted(matching, key=lambda m: m.priority)
