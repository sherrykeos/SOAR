"""
Embedding models package for SOAR.
Provides base interface, local BGE-M3 model adapter, and deterministic mock embedding model for testing.
"""

from .base import BaseEmbeddingModel
from .bge_m3 import BGEM3EmbeddingModel
from .mock import MockEmbeddingModel

__all__ = [
    "BaseEmbeddingModel",
    "BGEM3EmbeddingModel",
    "MockEmbeddingModel",
]
