import tempfile
import unittest
from pathlib import Path

from app.embeddings.mock import MockEmbeddingModel
from app.vector_store.chroma import ChromaVectorStore


class TestVectorStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.persist_dir = Path(self.temp_dir.name)
        self.embedding_model = MockEmbeddingModel(dimension=256)
        self.vector_store = ChromaVectorStore(
            collection_name="test_collection",
            persist_directory=self.persist_dir,
            embedding_model=self.embedding_model,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_and_count_documents(self):
        docs = [
            "Document 1: On-premise air-gapped sovereign AI architecture.",
            "Document 2: Local SQLite metadata and Chroma vector database setup.",
            "Document 3: Agent planning and execution loop with tool execution.",
        ]
        metadatas = [
            {"category": "architecture", "doc_type": "spec"},
            {"category": "database", "doc_type": "spec"},
            {"category": "agent", "doc_type": "code"},
        ]
        doc_ids = ["doc-1", "doc-2", "doc-3"]

        added_ids = self.vector_store.add_documents(
            documents=docs,
            metadatas=metadatas,
            ids=doc_ids,
        )

        self.assertEqual(added_ids, doc_ids)
        self.assertEqual(self.vector_store.count(), 3)

    def test_similarity_search_by_text(self):
        docs = [
            "Document 1: On-premise air-gapped sovereign AI architecture.",
            "Document 2: Local SQLite metadata and Chroma vector database setup.",
        ]
        metadatas = [
            {"category": "architecture"},
            {"category": "database"},
        ]
        self.vector_store.add_documents(documents=docs, metadatas=metadatas, ids=["doc-1", "doc-2"])

        # Search for exact match to doc-1 text
        results = self.vector_store.similarity_search(
            query="Document 1: On-premise air-gapped sovereign AI architecture.",
            k=2,
        )

        self.assertEqual(len(results), 2)
        top_result = results[0]
        self.assertEqual(top_result["id"], "doc-1")
        self.assertEqual(top_result["metadata"]["category"], "architecture")
        self.assertIsNotNone(top_result["score"])

    def test_similarity_search_with_filter(self):
        docs = ["Doc A in finance", "Doc B in engineering", "Doc C in finance"]
        metadatas = [{"dept": "finance"}, {"dept": "engineering"}, {"dept": "finance"}]
        self.vector_store.add_documents(documents=docs, metadatas=metadatas, ids=["a", "b", "c"])

        filtered_results = self.vector_store.similarity_search(
            query="Doc B in engineering",
            k=5,
            where={"dept": "finance"},
        )

        # Should only return finance docs
        self.assertEqual(len(filtered_results), 2)
        returned_ids = {r["id"] for r in filtered_results}
        self.assertEqual(returned_ids, {"a", "c"})

    def test_get_and_delete_documents(self):
        docs = ["Unique content to delete"]
        ids = self.vector_store.add_documents(documents=docs, ids=["del-1"])

        fetched = self.vector_store.get_document("del-1")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["id"], "del-1")
        self.assertEqual(fetched["document"], "Unique content to delete")

        deleted = self.vector_store.delete_documents(["del-1"])
        self.assertTrue(deleted)
        self.assertEqual(self.vector_store.count(), 0)
        self.assertIsNone(self.vector_store.get_document("del-1"))

    def test_persistence_across_instances(self):
        # Add a document in instance 1
        self.vector_store.add_documents(
            documents=["Persistent document text"],
            metadatas=[{"source": "test"}],
            ids=["persist-1"],
        )
        self.assertEqual(self.vector_store.count(), 1)

        # Create a new instance pointing to the same directory
        reopened_store = ChromaVectorStore(
            collection_name="test_collection",
            persist_directory=self.persist_dir,
            embedding_model=self.embedding_model,
        )

        self.assertEqual(reopened_store.count(), 1)
        doc = reopened_store.get_document("persist-1")
        self.assertIsNotNone(doc)
        self.assertEqual(doc["document"], "Persistent document text")


if __name__ == "__main__":
    unittest.main()
