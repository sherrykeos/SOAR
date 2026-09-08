import hashlib
import math
import random
from typing import List

from .base import BaseEmbeddingModel


class MockEmbeddingModel(BaseEmbeddingModel):
    """
    Deterministic Mock Embedding Model for testing and CI/air-gapped unit tests.
    Generates deterministic pseudo-random unit vectors based on content hash.
    Requires no heavy dependencies, model downloads, or GPU.
    """

    def __init__(self, dimension: int = 1024, model_name: str = "mock-bge-m3"):
        self._dimension = dimension
        self._model_name = model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def _generate_vector(self, text: str) -> List[float]:
        # Hash text to create a deterministic seed
        hash_digest = hashlib.sha256(text.encode("utf-8")).digest()
        seed_val = int.from_bytes(hash_digest[:8], byteorder="big")
        
        rng = random.Random(seed_val)
        raw_vec = [rng.gauss(0, 1) for _ in range(self._dimension)]
        
        # Normalize to unit length (L2 norm)
        norm = math.sqrt(sum(x * x for x in raw_vec))
        if norm > 0:
            return [x / norm for x in raw_vec]
        return [0.0] * self._dimension

    def embed_text(self, text: str) -> List[float]:
        return self._generate_vector(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        return self._generate_vector(query)
