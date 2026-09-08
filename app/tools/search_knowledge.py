import logging
from typing import Any, Dict, List, Optional

from app.embeddings.base import BaseEmbeddingModel
from app.vector_store.base import BaseVectorStore
from .base import BaseTool

logger = logging.getLogger(__name__)


class SearchKnowledgeTool(BaseTool):
    """
    Tool for searching the local SOAR organizational knowledge base.
    Uses semantic similarity search over local persistent ChromaDB vectors.
    Supports dependency injection for embedding models and vector stores.
    100% air-gapped and local.
    """

    def __init__(
        self,
        embedding_model: Optional[BaseEmbeddingModel] = None,
        vector_store: Optional[BaseVectorStore] = None,
        collection_name: str = "soar_knowledge",
        persist_directory: str = "data/chroma",
        default_top_k: int = 5,
    ):
        self._embedding_model = embedding_model
        self._vector_store = vector_store
        self._collection_name = collection_name
        self._persist_directory = persist_directory
        self._default_top_k = default_top_k

    @property
    def name(self) -> str:
        return "search_knowledge"

    @property
    def description(self) -> str:
        return (
            "Search the local SOAR organizational knowledge base for relevant information "
            "using semantic similarity retrieval."
        )

    @property
    def parameters(self) -> dict[str, dict[str, Any]]:
        return {
            "query": {
                "type": "string",
                "description": "Semantic search query string.",
                "required": True,
            },
            "top_k": {
                "type": "integer",
                "description": "Maximum number of relevant knowledge chunks to return (default: 5).",
                "required": False,
            },
        }

    def _get_embedding_model(self) -> BaseEmbeddingModel:
        """Lazily instantiates the default local BGE-M3 embedding model if not injected."""
        if self._embedding_model is None:
            from app.embeddings.bge_m3 import BGEM3EmbeddingModel

            self._embedding_model = BGEM3EmbeddingModel()
        return self._embedding_model

    def _get_vector_store(self) -> BaseVectorStore:
        """Lazily instantiates the default ChromaVectorStore if not injected."""
        if self._vector_store is None:
            from app.vector_store.chroma import ChromaVectorStore

            embedding_model = self._get_embedding_model()
            self._vector_store = ChromaVectorStore(
                collection_name=self._collection_name,
                persist_directory=self._persist_directory,
                embedding_model=embedding_model,
            )
        return self._vector_store

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Executes semantic search over local indexed knowledge chunks.
        Returns a structured dictionary with retrieved text and metadata.
        """
        raw_query = kwargs.get("query") or kwargs.get("search_query") or kwargs.get("q")
        raw_top_k = kwargs.get("top_k", kwargs.get("k", self._default_top_k))

        # 1. Validate query
        if raw_query is None or not isinstance(raw_query, str) or not raw_query.strip():
            return {
                "status": "error",
                "query": "" if raw_query is None else str(raw_query),
                "error": "Missing or empty required parameter 'query'.",
                "results": [],
            }

        query = raw_query.strip()

        # 2. Validate top_k
        try:
            top_k = int(raw_top_k)
            if top_k <= 0:
                return {
                    "status": "error",
                    "query": query,
                    "error": f"Invalid top_k '{raw_top_k}': must be a positive integer greater than 0.",
                    "results": [],
                }
        except (ValueError, TypeError):
            return {
                "status": "error",
                "query": query,
                "error": f"Invalid top_k '{raw_top_k}': must be a valid integer.",
                "results": [],
            }

        # 3. Perform similarity search
        try:
            embedding_model = self._get_embedding_model()
            query_embedding = embedding_model.embed_query(query)
            vector_store = self._get_vector_store()
            raw_results = vector_store.similarity_search(
                query=query,
                k=top_k,
                query_embedding=query_embedding,
            )
        except Exception as e:
            logger.error(f"Failed to execute semantic search in vector store: {e}", exc_info=True)
            return {
                "status": "error",
                "query": query,
                "error": f"Vector retrieval error: {str(e)}",
                "results": [],
            }

        # 4. Format structured results
        formatted_results: List[Dict[str, Any]] = []
        for item in raw_results:
            text = item.get("document") or item.get("text") or ""
            raw_score = item.get("score")
            score = None
            if raw_score is not None:
                try:
                    score = round(float(raw_score), 4)
                except (ValueError, TypeError):
                    score = None

            raw_meta = item.get("metadata") or {}
            # Filter out internal dummy flags like '_indexed'
            clean_meta = {k: v for k, v in raw_meta.items() if not k.startswith("_")}

            # Structure core citation/source metadata clearly
            metadata_dict: Dict[str, Any] = {
                "document_id": clean_meta.get("document_id"),
                "filename": clean_meta.get("filename"),
                "source_path": clean_meta.get("source_path"),
                "page_number": clean_meta.get("page_number"),
                "slide_number": clean_meta.get("slide_number"),
                "content_type": clean_meta.get("content_type"),
            }
            # Add any additional extracted metadata
            for k, v in clean_meta.items():
                if k not in metadata_dict:
                    metadata_dict[k] = v

            formatted_results.append(
                {
                    "text": text,
                    "score": score,
                    "metadata": metadata_dict,
                }
            )

        response: Dict[str, Any] = {
            "status": "success",
            "query": query,
            "count": len(formatted_results),
            "results": formatted_results,
        }

        if not formatted_results:
            response["message"] = "No relevant documents found matching query."

        return response
