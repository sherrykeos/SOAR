import hashlib
import os
import tempfile
import uuid
from pathlib import Path
from typing import List, Optional

from app.vision.base import BaseVisionProcessor
from .base import BaseExtractor, DocumentIngestionResult, ExtractedElement


class PDFExtractor(BaseExtractor):
    """
    Extracts text and page structure from PDF documents using PyMuPDF.
    Includes automated heuristic detection for scanned/raster-only PDF files
    and integrates BaseVisionProcessor to render and OCR scanned PDF pages locally.
    """

    def __init__(self, vision_processor: Optional[BaseVisionProcessor] = None):
        self.vision_processor = vision_processor

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

            # 1. First pass: extract standard text layer
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

            # 2. Heuristic for scanned / image-only PDFs
            is_scanned = (total_text_length < 10) or (len(elements) == 0)

            if is_scanned:
                # If vision processor is available, render pages and perform vision OCR
                if self.vision_processor is not None:
                    scanned_elements: List[ExtractedElement] = []
                    for page_num in range(total_pages):
                        page = doc[page_num]
                        pix = page.get_pixmap(dpi=150)
                        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                            tmp_path = Path(tmp_file.name)

                        try:
                            pix.save(str(tmp_path))
                            ocr_text = self.vision_processor.extract_text_ocr(tmp_path)
                            description = self.vision_processor.describe_image(tmp_path)

                            # Combine OCR text with visual description if distinct
                            combined_text_parts = []
                            if ocr_text and ocr_text.strip():
                                combined_text_parts.append(ocr_text.strip())
                            if description and description.strip() and description != ocr_text:
                                combined_text_parts.append(f"[Visual Layout]: {description.strip()}")

                            page_text = "\n\n".join(combined_text_parts) if combined_text_parts else f"[Page {page_num + 1} Image]"

                            scanned_elements.append(
                                ExtractedElement(
                                    text=page_text,
                                    metadata={
                                        "filename": filename,
                                        "source_path": str(path),
                                        "file_type": "pdf",
                                        "page_number": page_num + 1,
                                        "total_pages": total_pages,
                                        "is_scanned": True,
                                        "needs_ocr": False,
                                        "content_type": "scanned_page_vision_ocr",
                                    },
                                )
                            )
                        finally:
                            if tmp_path.exists():
                                try:
                                    os.unlink(tmp_path)
                                except Exception:
                                    pass

                    if scanned_elements:
                        return DocumentIngestionResult(
                            document_id=doc_id,
                            filename=filename,
                            source_path=str(path),
                            file_type="pdf",
                            file_size=file_size,
                            content_hash=content_hash,
                            elements=scanned_elements,
                            is_scanned=True,
                            needs_ocr=False,
                            status="success",
                        )

                # Fallback placeholder if no vision processor is configured
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
