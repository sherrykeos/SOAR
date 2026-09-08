from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional


class BaseVisionProcessor(ABC):
    """
    Abstract Base Class for Vision Processors in SOAR.
    Provides standardized interfaces for extracting descriptions, visual semantics,
    OCR text, and metadata from local image files.
    """

    @abstractmethod
    def process_image(self, image_path: str | Path, **kwargs: Any) -> Dict[str, Any]:
        """
        Processes an image and returns structured metadata, visual features,
        and textual annotations.
        """
        pass

    @abstractmethod
    def describe_image(self, image_path: str | Path, **kwargs: Any) -> str:
        """
        Generates a textual description/summary of the image content for knowledge indexing.
        """
        pass

    @abstractmethod
    def extract_text_ocr(self, image_path: str | Path, **kwargs: Any) -> str:
        """
        Performs visual text extraction / OCR on an image (e.g., scanned document page, receipt, diagram).
        """
        pass


class MockVisionProcessor(BaseVisionProcessor):
    """
    Deterministic Mock Vision Processor for testing and air-gapped environments
    without requiring heavy local vision models (e.g. Qwen2.5-VL).
    Generates structured semantic descriptions and simulated OCR text based on image metadata.
    """

    def __init__(
        self,
        default_description_prefix: str = "Image analysis:",
        default_ocr_prefix: str = "[OCR Extracted Text]:",
    ):
        self.default_description_prefix = default_description_prefix
        self.default_ocr_prefix = default_ocr_prefix

    def process_image(self, image_path: str | Path, **kwargs: Any) -> Dict[str, Any]:
        path = Path(image_path).resolve()
        filename = path.name

        try:
            from PIL import Image

            with Image.open(path) as img:
                width, height = img.size
                format_name = img.format or path.suffix.lstrip(".").upper()
                mode = img.mode
        except Exception:
            width, height = 0, 0
            format_name = path.suffix.lstrip(".").upper()
            mode = "UNKNOWN"

        description = self.describe_image(path, width=width, height=height, format=format_name, mode=mode)
        ocr_text = self.extract_text_ocr(path, width=width, height=height, format=format_name)

        return {
            "source_path": str(path),
            "filename": filename,
            "format": format_name,
            "width": width,
            "height": height,
            "mode": mode,
            "description": description,
            "ocr_text": ocr_text,
        }

    def describe_image(self, image_path: str | Path, **kwargs: Any) -> str:
        path = Path(image_path).resolve()
        filename = path.name
        width = kwargs.get("width")
        height = kwargs.get("height")
        format_name = kwargs.get("format")

        if width is None or height is None:
            try:
                from PIL import Image

                with Image.open(path) as img:
                    width, height = img.size
                    format_name = img.format or path.suffix.lstrip(".").upper()
            except Exception:
                width, height = "unknown", "unknown"
                format_name = path.suffix.lstrip(".").upper()

        return (
            f"{self.default_description_prefix} Image file '{filename}' "
            f"(Format: {format_name}, Dimensions: {width}x{height} pixels). "
            f"Visual asset for multimodal knowledge base."
        )

    def extract_text_ocr(self, image_path: str | Path, **kwargs: Any) -> str:
        path = Path(image_path).resolve()
        filename = path.name
        return f"{self.default_ocr_prefix} Scanned textual content from image '{filename}'."
