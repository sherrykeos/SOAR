import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from .base import BaseEmbeddingModel

logger = logging.getLogger(__name__)


class BGEM3EmbeddingModel(BaseEmbeddingModel):
    """
    Local BGE-M3 embedding model adapter using SentenceTransformers.
    Supports lazy model loading, local model directories, CPU/GPU execution, and offline guarantees.
    """

    def __init__(
        self,
        model_name_or_path: str = "BAAI/bge-m3",
        dimension: int = 1024,
        device: Optional[str] = None,
        normalize_embeddings: bool = True,
        batch_size: int = 32,
        model_kwargs: Optional[Dict[str, Any]] = None,
    ):
        self._model_name_or_path = str(model_name_or_path)
        self._dimension = dimension
        self._device = device
        self._normalize_embeddings = normalize_embeddings
        self._batch_size = batch_size
        self._model_kwargs = model_kwargs or {}
        self._model = None

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name_or_path

    def _get_model(self):
        """Lazy loads the SentenceTransformer model on first usage."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as e:
                raise ImportError(
                    "The `sentence-transformers` package is required to use BGEM3EmbeddingModel. "
                    "Install it via `pip install sentence-transformers`."
                ) from e

            # If path points to an existing local directory, resolve it
            target_path = self._model_name_or_path
            local_path = Path(target_path)
            if local_path.exists():
                target_path = str(local_path.resolve())

            logger.info(f"Loading embedding model: {target_path} on device={self._device}")
            self._model = SentenceTransformer(
                model_name_or_path=target_path,
                device=self._device,
                **self._model_kwargs,
            )
        return self._model

    def embed_text(self, text: str) -> List[float]:
        """Generates an embedding vector for a single text string."""
        model = self._get_model()
        embedding = model.encode(
            text,
            normalize_embeddings=self._normalize_embeddings,
            show_progress_bar=False,
        )
        return embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a list of text strings in batches."""
        if not texts:
            return []
        model = self._get_model()
        embeddings = model.encode(
            texts,
            batch_size=self._batch_size,
            normalize_embeddings=self._normalize_embeddings,
            show_progress_bar=False,
        )
        return embeddings.tolist() if hasattr(embeddings, "tolist") else [list(e) for e in embeddings]

    def embed_query(self, query: str) -> List[float]:
        """Generates an embedding vector for a search query string."""
        return self.embed_text(query)
