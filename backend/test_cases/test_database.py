import os
import tempfile
import unittest
from pathlib import Path

from app.database.connection import get_connection, get_db_connection
from app.database.repository import DatabaseManager
from app.database.schema import create_tables


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = Path(self.temp_dir.name) / "test_soar.db"
        self.db = DatabaseManager(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_schema_creation_and_connection(self):
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {row["name"] for row in cursor.fetchall()}

        expected_tables = {"documents", "agent_runs", "agent_steps", "audit_logs"}
        self.assertTrue(expected_tables.issubset(tables))

    def test_document_crud(self):
        # Insert document
        doc = self.db.insert_document(
            filename="test_report.pdf",
            source_path="inputs/test_report.pdf",
            file_type="pdf",
            file_size=10240,
            content_hash="hash123abc456",
        )
        self.assertIsNotNone(doc)
        doc_id = doc["id"]
        self.assertEqual(doc["filename"], "test_report.pdf")
        self.assertEqual(doc["content_hash"], "hash123abc456")

        # Get by ID
        fetched = self.db.get_document(doc_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["file_type"], "pdf")

        # Get by hash
        by_hash = self.db.get_document_by_hash("hash123abc456")
        self.assertIsNotNone(by_hash)
        self.assertEqual(by_hash["id"], doc_id)

        # List documents
        docs = self.db.list_documents()
        self.assertEqual(len(docs), 1)

        # Delete document
        deleted = self.db.delete_document(doc_id)
        self.assertTrue(deleted)
        self.assertIsNone(self.db.get_document(doc_id))
        self.assertEqual(len(self.db.list_documents()), 0)

    def test_agent_runs_and_steps(self):
        # Create Run
        run = self.db.create_agent_run(
            task="Analyze inspection report",
            model_used="qwen2.5:7b-instruct-q4_K_M",
            status="running",
        )
        run_id = run["id"]
        self.assertEqual(run["status"], "running")
        self.assertIsNone(run["completed_at"])

        # Record Steps
        step1 = self.db.record_agent_step(
            run_id=run_id,
            iteration=1,
            tool="pdf_reader",
            arguments={"file_path": "inputs/report.pdf"},
            result="Extracted text successfully",
            status="success",
        )
        self.assertEqual(step1["iteration"], 1)

        step2 = self.db.record_agent_step(
            run_id=run_id,
            iteration=2,
            tool="docx_creator",
            arguments={"output_path": "outputs/note.docx", "content": "Approved"},
            result="Document generated",
            status="success",
        )
        self.assertEqual(step2["iteration"], 2)

        # Retrieve steps
        steps = self.db.get_agent_steps(run_id)
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[0]["tool"], "pdf_reader")
        self.assertEqual(steps[1]["tool"], "docx_creator")

        # Update run status to completed
        updated = self.db.update_agent_run(run_id, status="completed")
        self.assertEqual(updated["status"], "completed")
        self.assertIsNotNone(updated["completed_at"])

        # List runs
        runs = self.db.list_agent_runs()
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["id"], run_id)

    def test_audit_logs(self):
        # Log audit events
        log1 = self.db.log_audit_event(
            event="DOCUMENT_INGESTED",
            component="DataLayer",
            details={"filename": "doc1.txt", "size": 512},
        )
        self.assertIsNotNone(log1["id"])

        log2 = self.db.log_audit_event(
            event="MODEL_INFERENCE_BLOCKED",
            component="SecurityManager",
            details="Network egress blocked",
        )

        # Retrieve all logs
        logs = self.db.get_audit_logs()
        self.assertEqual(len(logs), 2)

        # Filter logs by component
        sec_logs = self.db.get_audit_logs(component="SecurityManager")
        self.assertEqual(len(sec_logs), 1)
        self.assertEqual(sec_logs[0]["event"], "MODEL_INFERENCE_BLOCKED")


if __name__ == "__main__":
    unittest.main()
