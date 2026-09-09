import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
import fitz

from app.database import DatabaseManager
from app.embeddings.base import BaseEmbeddingModel
from app.embeddings.mock import MockEmbeddingModel
from app.ingestion.pipeline import IngestionPipeline
from app.models.adapter import ModelCapability
from app.models.manager import ModelManager
from app.models.mock import MockModel
from app.models.registry import ModelRegistry
from app.models.router import ModelRouter
from app.orchestrator import Orchestrator
from app.orchestrator.agent import Agent
from app.orchestrator.execution import Executor
from app.orchestrator.planning import Planner
from app.tools.registry import ToolRegistry
from app.tools.search_knowledge import SearchKnowledgeTool
from app.vector_store.base import BaseVectorStore
from app.vector_store.chroma import ChromaVectorStore


class FailingEmbeddingModel(BaseEmbeddingModel):
    """Failing embedding model for testing error handling."""

    @property
    def dimension(self) -> int:
        return 128

    @property
    def model_name(self) -> str:
        return "failing-model"

    def embed_text(self, text: str):
        raise RuntimeError("Embedding model GPU out-of-memory error")

    def embed_documents(self, texts):
        raise RuntimeError("Embedding model GPU out-of-memory error")

    def embed_query(self, query: str):
        raise RuntimeError("Embedding model GPU out-of-memory error")


class FailingVectorStore(BaseVectorStore):
    """Failing vector store for testing error handling."""

    def add_documents(self, documents, metadatas=None, ids=None, embeddings=None):
        raise RuntimeError("Disk I/O failure on vector store")

    def similarity_search(self, query: str, k: int = 4, where=None, query_embedding=None):
        raise RuntimeError("Chroma index corrupted or unreachable")

    def similarity_search_by_vector(self, embedding, k: int = 4, where=None):
        raise RuntimeError("Chroma index corrupted or unreachable")

    def get_document(self, doc_id: str):
        return None

    def delete_documents(self, ids):
        return False

    def count(self) -> int:
        return 0


class TestSearchKnowledgeTool(unittest.TestCase):
    """
    Comprehensive test suite for SearchKnowledgeTool and Local RAG Agent Integration.
    100% deterministic, local, and air-gapped using MockEmbeddingModel and temporary ChromaDB.
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.base_path = Path(self.temp_dir.name)
        self.chroma_path = self.base_path / "chroma"
        self.chroma_path.mkdir(parents=True, exist_ok=True)

        self.mock_embedding = MockEmbeddingModel(dimension=256, model_name="mock-bge-m3")
        self.vector_store = ChromaVectorStore(
            collection_name="test_soar_knowledge",
            persist_directory=str(self.chroma_path),
            embedding_model=self.mock_embedding,
        )

        self.search_tool = SearchKnowledgeTool(
            embedding_model=self.mock_embedding,
            vector_store=self.vector_store,
            default_top_k=3,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    # -------------------------------------------------------------
    # 1. Tool Registration & Schema Contracts
    # -------------------------------------------------------------
    def test_tool_registration(self):
        registry = ToolRegistry()
        registry.register(self.search_tool)
        self.assertIn("search_knowledge", registry.list_tool_names())
        retrieved_tool = registry.get("search_knowledge")
        self.assertIs(retrieved_tool, self.search_tool)

    def test_tool_name_and_description(self):
        self.assertEqual(self.search_tool.name, "search_knowledge")
        self.assertIn("organizational knowledge base", self.search_tool.description)
        self.assertIn("semantic similarity", self.search_tool.description)

    def test_parameter_schema(self):
        params = self.search_tool.parameters
        self.assertIn("query", params)
        self.assertTrue(params["query"]["required"])
        self.assertEqual(params["query"]["type"], "string")

        self.assertIn("top_k", params)
        self.assertFalse(params["top_k"]["required"])
        self.assertEqual(params["top_k"]["type"], "integer")

    # -------------------------------------------------------------
    # 2. Argument Validation
    # -------------------------------------------------------------
    def test_argument_validation_missing_query(self):
        # Missing query parameter in validate_arguments
        err = self.search_tool.validate_arguments({})
        self.assertIsNotNone(err)
        self.assertIn("Missing required parameter 'query'", err)

        # Empty string query in validate_arguments
        err = self.search_tool.validate_arguments({"query": "   "})
        self.assertIsNotNone(err)
        self.assertIn("Missing required parameter 'query'", err)

    def test_argument_validation_placeholder_key_rejection(self):
        # Prevent old planner placeholder bug
        err = self.search_tool.validate_arguments({"parameter_name": "query"})
        self.assertIsNotNone(err)
        self.assertIn("Invalid placeholder argument 'parameter_name'", err)

    def test_empty_query_execution_error(self):
        res = self.search_tool.execute(query="")
        self.assertEqual(res["status"], "error")
        self.assertIn("Missing or empty", res["error"])
        self.assertEqual(res["results"], [])

    def test_invalid_top_k_handling(self):
        # Negative top_k
        res1 = self.search_tool.execute(query="boiler safety", top_k=-2)
        self.assertEqual(res1["status"], "error")
        self.assertIn("must be a positive integer", res1["error"])

        # Zero top_k
        res2 = self.search_tool.execute(query="boiler safety", top_k=0)
        self.assertEqual(res2["status"], "error")
        self.assertIn("must be a positive integer", res2["error"])

        # Non-integer top_k
        res3 = self.search_tool.execute(query="boiler safety", top_k="invalid_number")
        self.assertEqual(res3["status"], "error")
        self.assertIn("must be a valid integer", res3["error"])

    # -------------------------------------------------------------
    # 3. Semantic Retrieval & Scoring
    # -------------------------------------------------------------
    def test_successful_semantic_search_and_score(self):
        docs = [
            "Boiler B-4 operational guidelines and pressure thresholds.",
            "Turbine cooling fan maintenance instructions.",
            "General employee vacation and holiday schedule.",
        ]
        metas = [
            {"filename": "boiler_manual.pdf", "page_number": 12, "content_type": "page_text"},
            {"filename": "turbine_ops.docx", "page_number": 3, "content_type": "paragraph"},
            {"filename": "hr_policy.pdf", "page_number": 1, "content_type": "page_text"},
        ]
        self.vector_store.add_documents(documents=docs, metadatas=metas)

        res = self.search_tool.execute(query="Boiler B-4 pressure limits", top_k=2)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["query"], "Boiler B-4 pressure limits")
        self.assertEqual(len(res["results"]), 2)
        self.assertEqual(res["count"], 2)

        top_result = res["results"][0]
        self.assertIn("text", top_result)
        self.assertIn("score", top_result)
        self.assertIsInstance(top_result["score"], float)
        self.assertIn("metadata", top_result)

    def test_no_results_behavior(self):
        # Search empty collection
        res = self.search_tool.execute(query="chemical safety MSDS", top_k=5)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["count"], 0)
        self.assertEqual(res["results"], [])
        self.assertIn("message", res)

    # -------------------------------------------------------------
    # 4. Metadata & Citation Preservation
    # -------------------------------------------------------------
    def test_metadata_preservation_pdf_and_pptx(self):
        docs = [
            "Safety inspection protocol for electrical generators.",
            "Slide 4: Quarterly turbine vibration metrics.",
        ]
        metas = [
            {
                "document_id": "doc_pdf_101",
                "filename": "generator_safety.pdf",
                "source_path": "/data/documents/generator_safety.pdf",
                "page_number": 14,
                "content_type": "page_text",
            },
            {
                "document_id": "doc_pptx_202",
                "filename": "vibration_metrics.pptx",
                "source_path": "/data/documents/vibration_metrics.pptx",
                "slide_number": 4,
                "content_type": "slide_text",
            },
        ]
        self.vector_store.add_documents(documents=docs, metadatas=metas)

        res = self.search_tool.execute(query="Safety inspection generator", top_k=5)
        self.assertEqual(res["status"], "success")

        # Verify PDF metadata
        pdf_res = next(r for r in res["results"] if r["metadata"]["filename"] == "generator_safety.pdf")
        self.assertEqual(pdf_res["metadata"]["document_id"], "doc_pdf_101")
        self.assertEqual(pdf_res["metadata"]["source_path"], "/data/documents/generator_safety.pdf")
        self.assertEqual(pdf_res["metadata"]["page_number"], 14)
        self.assertEqual(pdf_res["metadata"]["content_type"], "page_text")

        # Verify PPTX metadata
        pptx_res = next(r for r in res["results"] if r["metadata"]["filename"] == "vibration_metrics.pptx")
        self.assertEqual(pptx_res["metadata"]["document_id"], "doc_pptx_202")
        self.assertEqual(pptx_res["metadata"]["slide_number"], 4)
        self.assertEqual(pptx_res["metadata"]["content_type"], "slide_text")

    # -------------------------------------------------------------
    # 5. Robust Error Handling (Embedding & Vector Store Failures)
    # -------------------------------------------------------------
    def test_embedding_failure_handled_gracefully(self):
        failing_tool = SearchKnowledgeTool(
            embedding_model=FailingEmbeddingModel(),
            vector_store=self.vector_store,
        )
        res = failing_tool.execute(query="testing failure")
        self.assertEqual(res["status"], "error")
        self.assertIn("Vector retrieval error", res["error"])
        self.assertIn("GPU out-of-memory", res["error"])
        self.assertEqual(res["results"], [])

    def test_vector_store_failure_handled_gracefully(self):
        failing_tool = SearchKnowledgeTool(
            embedding_model=self.mock_embedding,
            vector_store=FailingVectorStore(),
        )
        res = failing_tool.execute(query="testing failure")
        self.assertEqual(res["status"], "error")
        self.assertIn("Vector retrieval error", res["error"])
        self.assertIn("corrupted or unreachable", res["error"])
        self.assertEqual(res["results"], [])

    # -------------------------------------------------------------
    # 6. Planner Discovery & Orchestrator Integration
    # -------------------------------------------------------------
    def test_planner_dynamically_discovers_search_knowledge(self):
        tool_reg = ToolRegistry()
        tool_reg.register(self.search_tool)

        mock_model = MockModel(
            model_id="mock-planner",
            capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
        )
        model_reg = ModelRegistry()
        model_reg.register(mock_model)
        model_mgr = ModelManager(model_registry=model_reg, model_router=ModelRouter(model_reg))

        planner = Planner(model_manager=model_mgr, tool_registry=tool_reg)
        tools_desc = planner._format_tools_description()

        self.assertIn("Tool: search_knowledge", tools_desc)
        self.assertIn("Description: Search the local SOAR organizational knowledge base", tools_desc)
        self.assertIn("query: Semantic search query string.", tools_desc)
        self.assertIn("top_k: Maximum number of relevant knowledge chunks", tools_desc)

    def test_orchestrator_default_registration(self):
        mock_model = MockModel(
            model_id="mock-orch",
            capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
        )
        model_reg = ModelRegistry()
        model_reg.register(mock_model)
        model_mgr = ModelManager(model_registry=model_reg, model_router=ModelRouter(model_reg))

        orch = Orchestrator(model_manager=model_mgr)
        self.assertIn("search_knowledge", orch.tool_registry.list_tool_names())
        registered_tool = orch.tool_registry.get("search_knowledge")
        self.assertIsInstance(registered_tool, SearchKnowledgeTool)

    # -------------------------------------------------------------
    # 7. Agent -> search_knowledge -> Observation Integration
    # -------------------------------------------------------------
    def test_agent_search_knowledge_observation_integration(self):
        # Index knowledge
        self.vector_store.add_documents(
            documents=["Boiler B-4 emergency shutdown procedure: Turn off main gas valve V-12."],
            metadatas=[{"filename": "emergency_ops.pdf", "page_number": 8}],
        )

        class RAGSequenceResponder:
            def __init__(self):
                self.count = 0

            def __call__(self, prompt: str) -> str:
                self.count += 1
                if self.count == 1:
                    # Plan iteration 1: search knowledge
                    return json.dumps({
                        "status": "continue",
                        "thought": "I need to search the knowledge base for boiler shutdown procedures.",
                        "steps": [
                            {
                                "tool": "search_knowledge",
                                "arguments": {
                                    "query": "Boiler B-4 emergency shutdown",
                                    "top_k": 3,
                                }
                            }
                        ]
                    })
                else:
                    # Plan iteration 2: Observe retrieved chunk and finish
                    return json.dumps({
                        "status": "complete",
                        "thought": "Found the shutdown procedure in knowledge base: Turn off valve V-12.",
                        "steps": []
                    })

        mock_responder = RAGSequenceResponder()
        mock_model = MockModel(
            model_id="rag-agent-model",
            capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
            response_fn=mock_responder,
        )

        model_reg = ModelRegistry()
        model_reg.register(mock_model)
        model_mgr = ModelManager(model_registry=model_reg, model_router=ModelRouter(model_reg))

        tool_reg = ToolRegistry()
        tool_reg.register(self.search_tool)

        planner = Planner(model_manager=model_mgr, tool_registry=tool_reg)
        executor = Executor(tool_registry=tool_reg)
        agent = Agent(planner=planner, executor=executor, max_iterations=5)

        state = agent.run("Find the emergency shutdown procedure for Boiler B-4.")

        self.assertEqual(state.status, "completed")
        self.assertEqual(state.iterations, 2)
        self.assertEqual(len(state.observations), 1)

        obs = state.observations[0]
        self.assertEqual(obs["tool"], "search_knowledge")
        self.assertEqual(obs["status"], "completed")

        res_data = obs["result"]
        self.assertIsInstance(res_data, dict)
        self.assertEqual(res_data["status"], "success")
        self.assertEqual(len(res_data["results"]), 1)
        self.assertIn("valve V-12", res_data["results"][0]["text"])
        self.assertEqual(res_data["results"][0]["metadata"]["filename"], "emergency_ops.pdf")
        self.assertEqual(res_data["results"][0]["metadata"]["page_number"], 8)

    # -------------------------------------------------------------
    # 8. End-to-End Deterministic RAG Pipeline
    # -------------------------------------------------------------
    def test_end_to_end_ingestion_and_rag_agent(self):
        # 1. Create a local sample PDF document
        doc_path = self.base_path / "safety_manual.pdf"
        safety_text = (
            "Boiler B-4 must be operated within the approved temperature and pressure limits. "
            "Any abnormal vibration or visible leakage requires inspection and corrective action."
        )
        pdf_doc = fitz.open()
        p = pdf_doc.new_page()
        p.insert_text((50, 72), safety_text)
        pdf_doc.save(doc_path)
        pdf_doc.close()

        # 2. Ingest document through IngestionPipeline into local ChromaVectorStore
        db_path = self.base_path / "soar_test.db"
        db = DatabaseManager(db_path=str(db_path))

        pipeline = IngestionPipeline(
            db_manager=db,
            vector_store=self.vector_store,
            embedding_model=self.mock_embedding,
        )
        ingest_res = pipeline.ingest_file(doc_path)
        self.assertEqual(ingest_res["status"], "success")
        self.assertGreater(ingest_res["chunks_indexed"], 0)

        # 3. Execute search_knowledge directly
        search_res = self.search_tool.execute(
            query="What are the safety requirements for Boiler B-4?",
            top_k=2,
        )
        self.assertEqual(search_res["status"], "success")
        self.assertGreater(search_res["count"], 0)
        retrieved_chunk = search_res["results"][0]
        self.assertIn("Boiler B-4", retrieved_chunk["text"])
        self.assertEqual(retrieved_chunk["metadata"]["filename"], "safety_manual.pdf")

        # 4. Agent reasoning loop over the ingested document
        class FullRAGResponder:
            def __init__(self):
                self.count = 0

            def __call__(self, prompt: str) -> str:
                self.count += 1
                if self.count == 1:
                    return json.dumps({
                        "status": "continue",
                        "thought": "I will search the knowledge base for Boiler B-4 safety rules.",
                        "steps": [
                            {
                                "tool": "search_knowledge",
                                "arguments": {
                                    "query": "What are the safety requirements for Boiler B-4?",
                                    "top_k": 3,
                                }
                            }
                        ]
                    })
                else:
                    return json.dumps({
                        "status": "complete",
                        "thought": "Safety requirements retrieved: operate within limits and inspect vibration/leakage.",
                        "steps": []
                    })

        rag_mock = MockModel(
            model_id="full-rag-mock",
            capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
            response_fn=FullRAGResponder(),
        )
        model_reg = ModelRegistry()
        model_reg.register(rag_mock)
        model_mgr = ModelManager(model_registry=model_reg, model_router=ModelRouter(model_reg))

        tool_reg = ToolRegistry()
        tool_reg.register(self.search_tool)

        planner = Planner(model_manager=model_mgr, tool_registry=tool_reg)
        executor = Executor(tool_registry=tool_reg)
        agent = Agent(planner=planner, executor=executor, max_iterations=5)

        final_state = agent.run("Find the safety requirements for Boiler B-4.")
        self.assertEqual(final_state.status, "completed")
        self.assertEqual(final_state.iterations, 2)
        self.assertEqual(len(final_state.observations), 1)
        self.assertEqual(final_state.observations[0]["tool"], "search_knowledge")
        self.assertEqual(final_state.observations[0]["status"], "completed")
        self.assertIn("approved temperature and pressure limits", final_state.observations[0]["result"]["results"][0]["text"])


if __name__ == "__main__":
    unittest.main()
