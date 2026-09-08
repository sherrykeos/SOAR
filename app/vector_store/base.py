from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseVectorStore(ABC):
    """
    Abstract Base Class for Vector Stores in SOAR.
    Provides standardized vector indexing, querying, deletion, and retrieval interfaces.
    """

    @abstractmethod
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None,
    ) -> List[str]:
        """
        Adds text chunks/documents and their metadata to the vector store.
        Returns the list of document IDs added.
        """
        pass

    @abstractmethod
    def similarity_search(
        self,
        query: str,
        k: int = 4,
        where: Optional[Dict[str, Any]] = None,
        query_embedding: Optional[List[float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Performs similarity search using query text or precomputed query embedding.
        Returns top-k matching documents with metadata and distance/score.
        """
        pass

    @abstractmethod
    def similarity_search_by_vector(
        self,
        embedding: List[float],
        k: int = 4,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Performs similarity search directly with an embedding vector.
        """
        pass

    @abstractmethod
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single document record by ID."""
        pass

    @abstractmethod
    def delete_documents(self, ids: List[str]) -> bool:
        """Deletes documents matching the given list of IDs."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Returns the total number of documents in the vector store."""
        pass
