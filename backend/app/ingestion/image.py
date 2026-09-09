import hashlib
import uuid
from pathlib import Path
from typing import List, Optional

from app.vision.base import BaseVisionProcessor, MockVisionProcessor
from .base import BaseExtractor, DocumentIngestionResult, ExtractedElement


class ImageExtractor(BaseExtractor):
    """
    Extracts metadata and visual semantic representations from image files
    (PNG, JPG, JPEG, WEBP, BMP, TIFF) using Pillow and an interchangeable BaseVisionProcessor.
    Treats images as first-class multimodal knowledge assets.
    """

    SUPPORTED_EXTS = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"]

    def __init__(self, vision_processor: Optional[BaseVisionProcessor] = None):
        self.vision_processor = vision_processor or MockVisionProcessor()

    @property
    def supported_extensions(self) -> List[str]:
        return self.SUPPORTED_EXTS

    def extract(self, file_path: str | Path) -> DocumentIngestionResult:
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")

        file_bytes = path.read_bytes()
        content_hash = hashlib.sha256(file_bytes).hexdigest()
        file_size = len(file_bytes)
        filename = path.name
        doc_id = str(uuid.uuid4())

        try:
            from PIL import Image
        except ImportError as e:
            raise ImportError(
                "Pillow is required for image ingestion. Install it via `pip install Pillow`."
            ) from e

        try:
            with Image.open(path) as img:
                img.verify()

            # Reopen to read dimensions and mode after verify()
            with Image.open(path) as img:
                width, height = img.size
                img_format = img.format or path.suffix.lstrip(".").upper()
                mode = img.mode

            # Generate semantic description via vision processor
            vision_result = self.vision_processor.process_image(path)
            description_text = vision_result.get("description") or self.vision_processor.describe_image(path)

            aspect_ratio = round(width / max(1, height), 2)

            element = ExtractedElement(
                text=description_text,
                metadata={
                    "filename": filename,
                    "source_path": str(path),
                    "file_type": "image",
                    "image_format": str(img_format).lower(),
                    "width": width,
                    "height": height,
                    "mode": mode,
                    "aspect_ratio": aspect_ratio,
                    "content_type": "image_description",
                },
            )

            return DocumentIngestionResult(
                document_id=doc_id,
                filename=filename,
                source_path=str(path),
                file_type="image",
                file_size=file_size,
                content_hash=content_hash,
                elements=[element],
                is_scanned=False,
                needs_ocr=False,
                status="success",
            )

        except Exception as e:
            return DocumentIngestionResult(
                document_id=doc_id,
                filename=filename,
                source_path=str(path),
                file_type="image",
                file_size=file_size,
                content_hash=content_hash,
                elements=[],
                status="error",
                error=f"Invalid or corrupt image file '{filename}': {str(e)}",
            )
