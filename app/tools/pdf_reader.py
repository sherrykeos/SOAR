from pathlib import Path
from typing import Any

from .base import BaseTool


class PDFReaderTool(BaseTool):

    @property
    def name(self) -> str:
        return "pdf_reader"

    @property
    def description(self) -> str:
        return (
            "Extracts text from a local PDF document. "
            "Pass 'file_path' (or 'path') as a parameter."
        )

    def execute(self, **kwargs: Any) -> str:
        file_path = kwargs.get("file_path") or kwargs.get("path")

        if not file_path:
            return "Error: Missing required parameter 'file_path' or 'path'."

        target_path = Path(file_path)

        if not target_path.exists():
            return f"Error: File not found at '{file_path}'."

        if target_path.is_dir():
            return f"Error: Path '{file_path}' is a directory, not a file."

        try:
            import fitz  # PyMuPDF
        except ImportError:
            return "Error: PyMuPDF (fitz) library is not installed."

        try:
            doc = fitz.open(target_path)
        except Exception as e:
            return f"Error: Invalid or corrupt PDF file '{file_path}': {str(e)}"

        try:
            if doc.is_encrypted:
                doc.close()
                return f"Error: PDF '{file_path}' is password-protected or encrypted."

            extracted_pages: list[str] = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text and text.strip():
                    extracted_pages.append(
                        f"--- Page {page_num + 1} ---\n{text.strip()}"
                    )

            doc.close()

            if not extracted_pages:
                return (
                    f"Warning: No extractable text found in PDF '{file_path}'. "
                    "The document may be empty or contain scanned images requiring OCR."
                )

            return "\n\n".join(extracted_pages)

        except Exception as e:
            return f"Error extracting text from PDF '{file_path}': {str(e)}"
