import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.embeddings.base import BaseEmbeddingModel
from .base import BaseVectorStore

logger = logging.getLogger(__name__)


class ChromaVectorStore(BaseVectorStore):
    """
    Local ChromaDB persistent vector store for SOAR.
    Persists vectors and document chunks locally to disk.
    Supports cosine similarity searches, metadata filtering, and custom embedding models.
    """

    def __init__(
        self,
        collection_name: str = "soar_knowledge",
        persist_directory: str | Path = "data/chroma",
        embedding_model: Optional[BaseEmbeddingModel] = None,
    ):
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory).resolve()
        self.embedding_model = embedding_model

        # Ensure persist directory exists
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self._client = None
        self._collection = None

    def _get_client(self):
        """Initializes and returns the Chroma persistent client."""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings
            except ImportError as e:
                raise ImportError(
                    "The `chromadb` package is required to use ChromaVectorStore. "
                    "Install it via `pip install chromadb`."
                ) from e

            # Create persistent client with telemetry disabled for air-gapped sovereign execution
            self._client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(anonymized_telemetry=False, is_persistent=True),
            )
        return self._client

    def _get_collection(self):
        """Gets or creates the Chroma collection configured with cosine distance."""
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None,
    ) -> List[str]:
        """
        Adds documents with metadata and embeddings to the local Chroma collection.
        """
        if not documents:
            return []

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]

        if embeddings is None and self.embedding_model is not None:
            embeddings = self.embedding_model.embed_documents(documents)

        collection = self._get_collection()

        add_kwargs: Dict[str, Any] = {
            "ids": ids,
            "documents": documents,
        }
        if metadatas is not None:
            cleaned_metadatas = []
            has_any = False
            for m in metadatas:
                if m and len(m) > 0:
                    cleaned_metadatas.append(dict(m))
                    has_any = True
                else:
                    cleaned_metadatas.append({"_indexed": "true"})
            if has_any:
                add_kwargs["metadatas"] = cleaned_metadatas

        if embeddings is not None:
            add_kwargs["embeddings"] = embeddings

        collection.add(**add_kwargs)
        return ids

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        where: Optional[Dict[str, Any]] = None,
        query_embedding: Optional[List[float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Performs similarity search using query string or optional precomputed query embedding.
        """
        if query_embedding is None and self.embedding_model is not None:
            query_embedding = self.embedding_model.embed_query(query)

        if query_embedding is not None:
            return self.similarity_search_by_vector(query_embedding, k=k, where=where)

        collection = self._get_collection()
        query_kwargs: Dict[str, Any] = {
            "query_texts": [query],
            "n_results": k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            query_kwargs["where"] = where

        results = collection.query(**query_kwargs)
        return self._format_query_results(results)

    def similarity_search_by_vector(
        self,
        embedding: List[float],
        k: int = 4,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Performs vector similarity search directly with an embedding vector.
        """
        collection = self._get_collection()
        query_kwargs: Dict[str, Any] = {
            "query_embeddings": [embedding],
            "n_results": k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            query_kwargs["where"] = where

        results = collection.query(**query_kwargs)
        return self._format_query_results(results)

    def _format_query_results(self, raw_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Formats Chroma query response into a clean list of result dicts."""
        formatted = []
        ids = raw_results.get("ids", [[]])[0]
        documents = raw_results.get("documents", [[]])[0]
        metadatas = raw_results.get("metadatas", [[]])[0]
        distances = raw_results.get("distances", [[]])[0] if "distances" in raw_results else [None] * len(ids)

        for i in range(len(ids)):
            dist = distances[i] if distances and i < len(distances) else None
            score = (1.0 - dist) if dist is not None else None
            meta = metadatas[i] if metadatas and i < len(metadatas) and metadatas[i] is not None else {}
            formatted.append(
                {
                    "id": ids[i],
                    "document": documents[i] if documents and i < len(documents) else None,
                    "metadata": meta,
                    "distance": dist,
                    "score": score,
                }
            )
        return formatted

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single document record from Chroma by ID."""
        collection = self._get_collection()
        res = collection.get(ids=[doc_id], include=["documents", "metadatas", "embeddings"])
        if res and res.get("ids") and len(res["ids"]) > 0:
            raw_meta = res["metadatas"][0] if res.get("metadatas") and len(res["metadatas"]) > 0 else None
            return {
                "id": res["ids"][0],
                "document": res["documents"][0] if res.get("documents") else None,
                "metadata": raw_meta if raw_meta is not None else {},
                "embedding": res["embeddings"][0] if res.get("embeddings") is not None and len(res["embeddings"]) > 0 else None,
            }
        return None

    def delete_documents(self, ids: List[str]) -> bool:
        """Deletes documents matching the provided IDs."""
        if not ids:
            return False
        collection = self._get_collection()
        collection.delete(ids=ids)
        return True

    def count(self) -> int:
        """Returns total document count in the collection."""
        collection = self._get_collection()
        return collection.count()

    def reset_collection(self) -> None:
        """Deletes and recreates the collection."""
        client = self._get_client()
        try:
            client.delete_collection(self.collection_name)
        except Exception:
            pass
        self._collection = None
