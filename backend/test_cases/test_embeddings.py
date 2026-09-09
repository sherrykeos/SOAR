import math
import unittest

from app.embeddings.base import BaseEmbeddingModel
from app.embeddings.bge_m3 import BGEM3EmbeddingModel
from app.embeddings.mock import MockEmbeddingModel


class TestEmbeddings(unittest.TestCase):
    def test_mock_embedding_properties(self):
        mock_model = MockEmbeddingModel(dimension=512, model_name="test-mock")
        self.assertEqual(mock_model.dimension, 512)
        self.assertEqual(mock_model.model_name, "test-mock")
        self.assertIsInstance(mock_model, BaseEmbeddingModel)

    def test_mock_embedding_determinism_and_norm(self):
        mock_model = MockEmbeddingModel(dimension=1024)
        vec1 = mock_model.embed_text("SOAR sovereign agent architecture")
        vec2 = mock_model.embed_text("SOAR sovereign agent architecture")
        vec3 = mock_model.embed_text("Completely different topic on aerospace engineering")

        # Determinism
        self.assertEqual(len(vec1), 1024)
        self.assertEqual(vec1, vec2)
        self.assertNotEqual(vec1, vec3)

        # L2 Normalization (norm should equal 1.0)
        norm = math.sqrt(sum(x * x for x in vec1))
        self.assertTrue(math.isclose(norm, 1.0, rel_tol=1e-5))

    def test_mock_embedding_batch_and_query(self):
        mock_model = MockEmbeddingModel()
        texts = ["Text document alpha", "Text document beta", "Text document gamma"]
        batch_vecs = mock_model.embed_documents(texts)

        self.assertEqual(len(batch_vecs), 3)
        for i, text in enumerate(texts):
            single_vec = mock_model.embed_text(text)
            self.assertEqual(batch_vecs[i], single_vec)

        query_vec = mock_model.embed_query("Text document alpha")
        self.assertEqual(query_vec, batch_vecs[0])

    def test_bge_m3_lazy_initialization(self):
        # BGEM3EmbeddingModel should initialize without immediately loading the model
        bge_model = BGEM3EmbeddingModel(
            model_name_or_path="BAAI/bge-m3",
            dimension=1024,
            device="cpu",
        )
        self.assertEqual(bge_model.dimension, 1024)
        self.assertEqual(bge_model.model_name, "BAAI/bge-m3")
        self.assertIsNone(bge_model._model)


if __name__ == "__main__":
    unittest.main()
