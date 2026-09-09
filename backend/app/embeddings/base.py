from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingModel(ABC):
    """
    Abstract Base Class for embedding models in SOAR.
    Provides standard interfaces for single text and batch document embeddings.
    """

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Returns the embedding vector dimension."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns the name or identifier of the embedding model."""
        pass

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generates an embedding vector for a single string."""
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generates embedding vectors for a batch of strings."""
        pass

    def embed_query(self, query: str) -> List[float]:
        """
        Generates an embedding vector for a search query.
        Defaults to calling embed_text unless overridden.
        """
        return self.embed_text(query)
