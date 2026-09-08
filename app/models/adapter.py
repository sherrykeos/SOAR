from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Set


class ModelCapability:
    GENERAL = "general"
    REASONING = "reasoning"
    CODING = "coding"
    VISION = "vision"
    DOCUMENT = "document"


@dataclass
class ModelMetadata:
    model_id: str
    provider: str
    capabilities: Set[str] = field(default_factory=lambda: {ModelCapability.GENERAL})
    priority: int = 100  # Lower number indicates higher priority/preference


class ModelAdapter(ABC):

    @property
    @abstractmethod
    def metadata(self) -> ModelMetadata:
        """Returns the metadata associated with this model adapter."""
        pass

    @property
    def model_id(self) -> str:
        return self.metadata.model_id

    @property
    def provider(self) -> str:
        return self.metadata.provider

    @property
    def capabilities(self) -> Set[str]:
        return self.metadata.capabilities

    @property
    def priority(self) -> int:
        return self.metadata.priority

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        think: bool = False,
        **kwargs: Any,
    ) -> str:
        """Generates text from the given prompt."""
        pass
