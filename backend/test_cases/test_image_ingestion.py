import tempfile
import unittest
from pathlib import Path
from PIL import Image

from app.database.repository import DatabaseManager
from app.embeddings.mock import MockEmbeddingModel
from app.ingestion.image import ImageExtractor
from app.ingestion.pipeline import IngestionPipeline
from app.vector_store.chroma import ChromaVectorStore
from app.vision.base import MockVisionProcessor


class TestImageIngestion(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.base_path = Path(self.temp_dir.name)

        # Create test images in different formats
        self.png_path = self.base_path / "diagram.png"
        img_png = Image.new("RGB", (640, 480), color="blue")
        img_png.save(self.png_path, format="PNG")

        self.jpg_path = self.base_path / "photo.jpg"
        img_jpg = Image.new("RGB", (800, 600), color="red")
        img_jpg.save(self.jpg_path, format="JPEG")

        self.bmp_path = self.base_path / "schema.bmp"
        img_bmp = Image.new("RGB", (320, 240), color="green")
        img_bmp.save(self.bmp_path, format="BMP")

        self.corrupt_path = self.base_path / "corrupt.png"
        self.corrupt_path.write_bytes(b"NOT_A_VALID_IMAGE_BYTES_12345")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_image_extractor_metadata_and_description(self):
        vision = MockVisionProcessor()
        extractor = ImageExtractor(vision_processor=vision)

        res = extractor.extract(self.png_path)
        self.assertEqual(res.status, "success")
        self.assertEqual(res.file_type, "image")
        self.assertEqual(len(res.elements), 1)

        elem = res.elements[0]
        self.assertIn("Image file 'diagram.png'", elem.text)
        self.assertEqual(elem.metadata["width"], 640)
        self.assertEqual(elem.metadata["height"], 480)
        self.assertEqual(elem.metadata["image_format"], "png")
        self.assertEqual(elem.metadata["aspect_ratio"], 1.33)

    def test_corrupt_image_handling(self):
        extractor = ImageExtractor()
        res = extractor.extract(self.corrupt_path)
        self.assertEqual(res.status, "error")
        self.assertIsNotNone(res.error)
        self.assertIn("Invalid or corrupt image", res.error)

    def test_image_pipeline_ingestion(self):
        db_path = self.base_path / "test_soar.db"
        chroma_dir = self.base_path / "chroma"
        db = DatabaseManager(db_path=db_path)
        embedding_model = MockEmbeddingModel(dimension=256)
        vector_store = ChromaVectorStore(
            collection_name="test_image_kb",
            persist_directory=chroma_dir,
            embedding_model=embedding_model,
        )

        pipeline = IngestionPipeline(
            db_manager=db,
            vector_store=vector_store,
            embedding_model=embedding_model,
        )

        result = pipeline.ingest_file(self.jpg_path)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["file_type"], "image")
        self.assertEqual(result["chunks_indexed"], 1)

        # Verify SQLite registration
        doc = db.get_document(result["document_id"])
        self.assertIsNotNone(doc)
        self.assertEqual(doc["filename"], "photo.jpg")
        self.assertEqual(doc["file_type"], "image")

        # Verify Chroma vector indexing
        search_results = vector_store.similarity_search(query="photo.jpg", k=1)
        self.assertEqual(len(search_results), 1)
        self.assertEqual(search_results[0]["metadata"]["filename"], "photo.jpg")
        self.assertEqual(search_results[0]["metadata"]["width"], 800)


if __name__ == "__main__":
    unittest.main()
