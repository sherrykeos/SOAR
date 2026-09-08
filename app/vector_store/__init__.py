"""
Vector store package for SOAR.
Provides base vector store interface and persistent local ChromaDB implementation.
"""

from .base import BaseVectorStore
from .chroma import ChromaVectorStore

__all__ = [
    "BaseVectorStore",
    "ChromaVectorStore",
]
