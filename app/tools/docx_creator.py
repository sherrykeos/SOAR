import os
from pathlib import Path
from typing import Any

from .base import BaseTool


class DOCXCreatorTool(BaseTool):

    @property
    def name(self) -> str:
        return "docx_creator"

    @property
    def description(self) -> str:
        return "Creates a local DOCX document with a title and paragraph content."

    @property
    def parameters(self) -> dict[str, dict[str, Any]]:
        return {
            "output_path": {
                "type": "string",
                "description": "Path where the generated DOCX file will be saved.",
                "required": True,
            },
            "title": {
                "type": "string",
                "description": "Document title or heading.",
                "required": False,
            },
            "content": {
                "type": "string",
                "description": "Text body or paragraph content for the document.",
                "required": True,
            },
        }

    def execute(self, **kwargs: Any) -> str:
        output_path = (
            kwargs.get("output_path")
            or kwargs.get("file_path")
            or kwargs.get("path")
        )

        if not output_path:
            return "Error: Missing required parameter 'output_path' (or 'file_path')."

        title = str(kwargs.get("title", "")).strip()
        content = str(kwargs.get("content", "")).strip()

        try:
            import docx
        except ImportError:
            return "Error: python-docx library is not installed."

        try:
            target_path = Path(output_path)

            # Ensure parent directory exists
            if target_path.parent and not target_path.parent.exists():
                target_path.parent.mkdir(parents=True, exist_ok=True)

            doc = docx.Document()

            if title:
                doc.add_heading(title, level=0)

            if content:
                # Support multi-paragraph content split by blank lines or newlines
                paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
                if not paragraphs:
                    paragraphs = [p.strip() for p in content.splitlines() if p.strip()]

                for p in paragraphs:
                    doc.add_paragraph(p)

            doc.save(str(target_path))

            return f"Successfully created DOCX document at '{output_path}'."

        except PermissionError:
            return f"Error: Permission denied when saving DOCX to '{output_path}'."
        except Exception as e:
            return f"Error creating DOCX document at '{output_path}': {str(e)}"
