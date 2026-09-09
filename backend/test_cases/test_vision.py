import tempfile
import unittest
from pathlib import Path
from PIL import Image
import fitz

from app.ingestion.image import ImageExtractor
from app.ingestion.pdf import PDFExtractor
from app.vision.base import BaseVisionProcessor, MockVisionProcessor
from app.vision.qwen import QwenVisionProcessor


class TestVision(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.base_path = Path(self.temp_dir.name)

        # Create a test image
        self.img_path = self.base_path / "diagram.png"
        img = Image.new("RGB", (400, 300), color="blue")
        img.save(self.img_path, format="PNG")

        # Create a scanned (blank) PDF
        self.scanned_pdf_path = self.base_path / "scanned_invoice.pdf"
        doc = fitz.open()
        p = doc.new_page()
        # Draw a small rectangle to simulate image-only content without text
        p.draw_rect(fitz.Rect(50, 50, 200, 200), color=(0, 0, 1), fill=(0.8, 0.8, 0.8))
        doc.save(self.scanned_pdf_path)
        doc.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_qwen_processor_configuration_and_encoding(self):
        proc = QwenVisionProcessor(
            model_name="qwen2.5vl:3b",
            base_url="http://localhost:11434",
            backend="ollama",
            temperature=0.1,
        )
        self.assertEqual(proc.model_name, "qwen2.5vl:3b")
        self.assertEqual(proc.backend, "ollama")
        self.assertEqual(proc.temperature, 0.1)
        self.assertIsInstance(proc, BaseVisionProcessor)

        # Test base64 image encoding
        b64_str = proc._encode_image(self.img_path)
        self.assertIsInstance(b64_str, str)
        self.assertTrue(len(b64_str) > 0)

        # Test invalid file paths
        with self.assertRaises(FileNotFoundError):
            proc._encode_image(self.base_path / "non_existent.png")
        with self.assertRaises(ValueError):
            proc._encode_image(self.base_path)

    def test_qwen_processor_unreachable_backend_error_handling(self):
        # Point to an invalid local port to verify clear error reporting
        proc = QwenVisionProcessor(
            model_name="qwen2.5vl:3b",
            base_url="http://127.0.0.1:59999",
            timeout=2,
        )
        with self.assertRaises(ConnectionError) as ctx:
            proc.describe_image(self.img_path)
        self.assertIn("Could not connect to local Ollama vision backend", str(ctx.exception))

    def test_mock_vision_processor_contracts(self):
        mock_proc = MockVisionProcessor(
            default_description_prefix="Test Description:",
            default_ocr_prefix="Test OCR:",
        )
        desc = mock_proc.describe_image(self.img_path)
        self.assertIn("Test Description:", desc)
        self.assertIn("diagram.png", desc)

        ocr = mock_proc.extract_text_ocr(self.img_path)
        self.assertIn("Test OCR:", ocr)
        self.assertIn("diagram.png", ocr)

        full_proc = mock_proc.process_image(self.img_path)
        self.assertEqual(full_proc["filename"], "diagram.png")
        self.assertEqual(full_proc["width"], 400)
        self.assertEqual(full_proc["height"], 300)
        self.assertEqual(full_proc["format"], "PNG")
        self.assertEqual(full_proc["description"], desc)
        self.assertEqual(full_proc["ocr_text"], ocr)

    def test_scanned_pdf_rendering_with_vision_processor(self):
        mock_proc = MockVisionProcessor()
        extractor = PDFExtractor(vision_processor=mock_proc)

        res = extractor.extract(self.scanned_pdf_path)
        self.assertEqual(res.status, "success")
        self.assertTrue(res.is_scanned)
        self.assertFalse(res.needs_ocr)
        self.assertEqual(len(res.elements), 1)

        elem = res.elements[0]
        self.assertEqual(elem.metadata["page_number"], 1)
        self.assertEqual(elem.metadata["content_type"], "scanned_page_vision_ocr")
        self.assertTrue(elem.metadata["is_scanned"])
        self.assertFalse(elem.metadata["needs_ocr"])
        self.assertIn("Scanned textual content from image", elem.text)

    def test_scanned_pdf_without_vision_processor_fallback(self):
        extractor = PDFExtractor(vision_processor=None)

        res = extractor.extract(self.scanned_pdf_path)
        self.assertEqual(res.status, "scanned_needs_ocr")
        self.assertTrue(res.is_scanned)
        self.assertTrue(res.needs_ocr)
        self.assertEqual(len(res.elements), 1)
        self.assertIn("[Scanned PDF Document", res.elements[0].text)

    def test_image_extractor_with_custom_vision_processor(self):
        mock_proc = MockVisionProcessor(default_description_prefix="Custom Vision:")
        extractor = ImageExtractor(vision_processor=mock_proc)

        res = extractor.extract(self.img_path)
        self.assertEqual(res.status, "success")
        self.assertEqual(res.file_type, "image")
        self.assertEqual(len(res.elements), 1)

        elem = res.elements[0]
        self.assertIn("Custom Vision:", elem.text)
        self.assertEqual(elem.metadata["width"], 400)
        self.assertEqual(elem.metadata["height"], 300)
        self.assertEqual(elem.metadata["aspect_ratio"], 1.33)


if __name__ == "__main__":
    unittest.main()
