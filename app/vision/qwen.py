import base64
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from .base import BaseVisionProcessor

logger = logging.getLogger(__name__)


class QwenVisionProcessor(BaseVisionProcessor):
    """
    Production Local Vision Processor using Qwen2.5-VL-3B-Instruct.
    Performs local, air-gapped visual scene understanding, diagram analysis, and OCR extraction.
    Zero cloud or external network API calls.
    """

    DEFAULT_MODEL = "qwen2.5vl:3b"

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        base_url: str = "http://localhost:11434",
        backend: str = "ollama",
        timeout: int = 180,
        temperature: float = 0.2,
    ):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.backend = backend
        self.timeout = timeout
        self.temperature = temperature

    def _encode_image(self, image_path: str | Path) -> str:
        """Reads a local image file and returns base64-encoded string."""
        path = Path(image_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")
        if not path.is_file():
            raise ValueError(f"Path is not a valid file: {path}")

        image_bytes = path.read_bytes()
        return base64.b64encode(image_bytes).decode("utf-8")

    def _generate(self, prompt: str, image_b64: str) -> str:
        """Executes local vision model inference via the selected backend."""
        if self.backend == "ollama":
            return self._generate_ollama(prompt, image_b64)
        else:
            raise ValueError(f"Unsupported vision backend '{self.backend}'. Supported backends: ['ollama']")

    def _generate_ollama(self, prompt: str, image_b64: str) -> str:
        """Executes vision inference using local Ollama instance."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
            "options": {
                "temperature": self.temperature,
            },
        }

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return (data.get("response") or "").strip()

        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(
                f"Could not connect to local Ollama vision backend at '{self.base_url}'. "
                "Ensure Ollama is installed and running locally ('ollama serve')."
            ) from e
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(
                f"Ollama vision inference error (HTTP {response.status_code}): {response.text}. "
                f"Ensure the vision model '{self.model_name}' is installed locally using 'ollama pull {self.model_name}'."
            ) from e
        except Exception as e:
            raise RuntimeError(f"Local vision model inference failed: {str(e)}") from e

    def describe_image(self, image_path: str | Path, **kwargs: Any) -> str:
        """
        Generates a dense visual semantic description of an image for knowledge retrieval.
        """
        image_b64 = self._encode_image(image_path)
        prompt = (
            kwargs.get("prompt")
            or "Describe this image in detail for a multimodal knowledge base. "
            "Explain the visual contents, key entities, diagrams, charts, labels, text, and overall structure."
        )
        return self._generate(prompt, image_b64)

    def extract_text_ocr(self, image_path: str | Path, **kwargs: Any) -> str:
        """
        Performs visual text extraction / OCR on an image or scanned document page.
        """
        image_b64 = self._encode_image(image_path)
        prompt = (
            kwargs.get("prompt")
            or "Perform optical character recognition (OCR) on this image. "
            "Extract all visible text, numbers, headings, tables, labels, and symbols verbatim. "
            "Preserve formatting and structure where possible."
        )
        return self._generate(prompt, image_b64)

    def process_image(self, image_path: str | Path, **kwargs: Any) -> Dict[str, Any]:
        """
        Processes an image and returns full structured visual metadata, description, and OCR text.
        """
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

        description = self.describe_image(path)
        ocr_text = self.extract_text_ocr(path)

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
