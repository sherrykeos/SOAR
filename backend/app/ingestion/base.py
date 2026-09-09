from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ExtractedElement:
    """
    Represents a discrete semantic unit or section extracted from a document
    (e.g., a PDF page, a DOCX paragraph/table, a PPTX slide, or an image description).
    """
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentIngestionResult:
    """
    Represents the output of extracting a raw document file.
    Carries extracted textual elements, scanned status, file metadata, and error details.
    """
    document_id: str
    filename: str
    source_path: str
    file_type: str
    file_size: int
    content_hash: str
    elements: List[ExtractedElement] = field(default_factory=list)
    is_scanned: bool = False
    needs_ocr: bool = False
    status: str = "success"  # "success", "duplicate", "scanned_needs_ocr", "error"
    error: Optional[str] = None


class BaseExtractor(ABC):
    """
    Abstract Base Class for file-type extractors in SOAR.
    Each extractor handles parsing a specific set of document formats into ExtractedElements.
    """

    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """List of lowercase file extensions supported by this extractor (e.g., ['.pdf'])."""
        pass

    @abstractmethod
    def extract(self, file_path: str | Path) -> DocumentIngestionResult:
        """
        Extracts content, structure, and metadata from the given file.
        """
        pass
