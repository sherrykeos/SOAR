import hashlib
import uuid
from pathlib import Path
from typing import List

from .base import BaseExtractor, DocumentIngestionResult, ExtractedElement


class PDFExtractor(BaseExtractor):
    """
    Extracts text and page structure from PDF documents using PyMuPDF.
    Includes automated heuristic detection for scanned/raster-only PDF files.
    """

    @property
    def supported_extensions(self) -> List[str]:
        return [".pdf"]

    def extract(self, file_path: str | Path) -> DocumentIngestionResult:
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {path}")

        file_bytes = path.read_bytes()
        content_hash = hashlib.sha256(file_bytes).hexdigest()
        file_size = len(file_bytes)
        filename = path.name
        doc_id = str(uuid.uuid4())

        try:
            import fitz  # PyMuPDF
        except ImportError as e:
            raise ImportError(
                "PyMuPDF is required for PDF extraction. Install it via `pip install PyMuPDF`."
            ) from e

        doc = None
        try:
            doc = fitz.open(path)

            if doc.is_encrypted:
                return DocumentIngestionResult(
                    document_id=doc_id,
                    filename=filename,
                    source_path=str(path),
                    file_type="pdf",
                    file_size=file_size,
                    content_hash=content_hash,
                    elements=[],
                    status="error",
                    error=f"PDF '{filename}' is password-protected or encrypted.",
                )

            total_pages = len(doc)
            elements: List[ExtractedElement] = []
            total_text_length = 0

            for page_num in range(total_pages):
                page = doc[page_num]
                text = (page.get_text() or "").strip()

                if text:
                    total_text_length += len(text)
                    elements.append(
                        ExtractedElement(
                            text=text,
                            metadata={
                                "filename": filename,
                                "source_path": str(path),
                                "file_type": "pdf",
                                "page_number": page_num + 1,
                                "total_pages": total_pages,
                                "content_type": "page_text",
                            },
                        )
                    )

            # Heuristic for scanned / image-only PDFs
            is_scanned = (total_text_length < 10) or (len(elements) == 0)

            if is_scanned:
                scanned_placeholder = (
                    f"[Scanned PDF Document: '{filename}'] "
                    f"No extractable text layer detected across {total_pages} page(s). "
                    f"Flagged for OCR / Vision ingestion pipeline."
                )
                elements = [
                    ExtractedElement(
                        text=scanned_placeholder,
                        metadata={
                            "filename": filename,
                            "source_path": str(path),
                            "file_type": "pdf",
                            "page_number": 1,
                            "total_pages": total_pages,
                            "is_scanned": True,
                            "needs_ocr": True,
                            "content_type": "scanned_notice",
                        },
                    )
                ]
                return DocumentIngestionResult(
                    document_id=doc_id,
                    filename=filename,
                    source_path=str(path),
                    file_type="pdf",
                    file_size=file_size,
                    content_hash=content_hash,
                    elements=elements,
                    is_scanned=True,
                    needs_ocr=True,
                    status="scanned_needs_ocr",
                )

            return DocumentIngestionResult(
                document_id=doc_id,
                filename=filename,
                source_path=str(path),
                file_type="pdf",
                file_size=file_size,
                content_hash=content_hash,
                elements=elements,
                is_scanned=False,
                needs_ocr=False,
                status="success",
            )

        except Exception as e:
            return DocumentIngestionResult(
                document_id=doc_id,
                filename=filename,
                source_path=str(path),
                file_type="pdf",
                file_size=file_size,
                content_hash=content_hash,
                elements=[],
                status="error",
                error=f"Error extracting PDF '{filename}': {str(e)}",
            )
        finally:
            if doc:
                doc.close()
