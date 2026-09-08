from pathlib import Path
from typing import Any

from .base import BaseTool


class PDFCreatorTool(BaseTool):

    @property
    def name(self) -> str:
        return "pdf_creator"

    @property
    def description(self) -> str:
        return (
            "Creates a local PDF document with a title and paragraph content. "
            "Pass 'output_path' (or 'file_path'), 'title', and 'content' as parameters."
        )

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
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
        except ImportError:
            return "Error: reportlab library is not installed."

        try:
            target_path = Path(output_path)

            # Ensure parent directory exists
            if target_path.parent and not target_path.parent.exists():
                target_path.parent.mkdir(parents=True, exist_ok=True)

            doc = SimpleDocTemplate(
                str(target_path),
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72,
            )

            styles = getSampleStyleSheet()
            story = []

            if title:
                # Add title
                story.append(Paragraph(title, styles["Title"]))
                story.append(Spacer(1, 14))

            if content:
                # Split into paragraphs
                paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
                if not paragraphs:
                    paragraphs = [p.strip() for p in content.splitlines() if p.strip()]

                body_style = styles["Normal"]
                body_style.fontSize = 11
                body_style.leading = 14

                for p in paragraphs:
                    story.append(Paragraph(p, body_style))
                    story.append(Spacer(1, 8))

            doc.build(story)

            return f"Successfully created PDF document at '{output_path}'."

        except PermissionError:
            return f"Error: Permission denied when saving PDF to '{output_path}'."
        except Exception as e:
            return f"Error creating PDF document at '{output_path}': {str(e)}"
