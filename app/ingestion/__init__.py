"""
Multimodal Knowledge Ingestion package for SOAR.
Provides modular extractors for PDF, DOCX, PPTX, and Images,
scanned-document detection, recursive character chunking,
and the end-to-end IngestionPipeline orchestrator.
"""

from .base import BaseExtractor, DocumentIngestionResult, ExtractedElement
from .chunker import BaseChunker, RecursiveCharacterChunker, TextChunk
from .docx import DOCXExtractor
from .image import ImageExtractor
from .pdf import PDFExtractor
from .pipeline import IngestionPipeline
from .pptx import PPTXExtractor

__all__ = [
    "BaseExtractor",
    "ExtractedElement",
    "DocumentIngestionResult",
    "BaseChunker",
    "RecursiveCharacterChunker",
    "TextChunk",
    "PDFExtractor",
    "DOCXExtractor",
    "PPTXExtractor",
    "ImageExtractor",
    "IngestionPipeline",
]
