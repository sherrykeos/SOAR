from abc import abstractmethod
from typing import Any

from .adapter import ModelAdapter, ModelMetadata


class BaseModel(ModelAdapter):
    """
    Backwards compatibility base class for existing model implementations.
    Inherits from ModelAdapter.
    """

    @property
    def metadata(self) -> ModelMetadata:
        return ModelMetadata(
            model_id="base-model",
            provider="generic",
        )

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        think: bool = False,
        **kwargs: Any,
    ) -> str:
        pass