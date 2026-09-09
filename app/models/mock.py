from typing import Any, Callable, Set

from .adapter import ModelAdapter, ModelCapability, ModelMetadata


class MockModel(ModelAdapter):

    def __init__(
        self,
        model_id: str = "mock-model",
        provider: str = "mock",
        capabilities: Set[str] | None = None,
        priority: int = 100,
        fixed_response: str = "Mock response from SOAR local model.",
        response_fn: Callable[[str], str] | None = None,
        available: bool = True,
    ):
        self._model_id = model_id
        self._provider = provider
        self._capabilities = capabilities or {ModelCapability.GENERAL}
        self._priority = priority
        self.fixed_response = fixed_response
        self.response_fn = response_fn
        self._available = available

    @property
    def metadata(self) -> ModelMetadata:
        return ModelMetadata(
            model_id=self._model_id,
            provider=self._provider,
            capabilities=self._capabilities,
            priority=self._priority,
        )

    def is_available(self) -> bool:
        return self._available

    def generate(
        self,
        prompt: str,
        *,
        think: bool = False,
        **kwargs: Any,
    ) -> str:
        if not self._available:
            raise RuntimeError(f"Mock model '{self._model_id}' is marked unavailable.")
        if self.response_fn is not None:
            return self.response_fn(prompt)
        return self.fixed_response
