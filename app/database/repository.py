import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .connection import get_connection, get_db_connection
from .schema import create_tables


class DatabaseManager:
    """
    Manages local SQLite metadata operations for SOAR.
    Coordinates document tracking, agent runs/steps logging, and audit logs.
    """

    def __init__(self, db_path: str | Path = "data/soar.db"):
        self.db_path = Path(db_path).resolve()
        # Initialize database and tables on startup
        with self._get_connection() as conn:
            create_tables(conn)

    def _get_connection(self):
        return get_db_connection(self.db_path)

    # -------------------------------------------------------------
    # Documents
    # -------------------------------------------------------------
    def insert_document(
        self,
        filename: str,
        source_path: str,
        file_type: str,
        file_size: int,
        content_hash: str,
        doc_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Inserts a new document record into metadata storage."""
        doc_id = doc_id or str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO documents (id, filename, source_path, file_type, file_size, content_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (doc_id, filename, source_path, file_type, file_size, content_hash, created_at),
            )
            conn.commit()

        return self.get_document(doc_id)  # type: ignore

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a document by its ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_document_by_hash(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieves a document by its SHA-256 / content hash to detect duplicates."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE content_hash = ?", (content_hash,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_documents(self) -> List[Dict[str, Any]]:
        """Lists all registered documents in the metadata database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def delete_document(self, doc_id: str) -> bool:
        """Deletes a document from the metadata database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.commit()
            return cursor.rowcount > 0

    # -------------------------------------------------------------
    # Files (Local File Storage Management)
    # -------------------------------------------------------------
    def insert_file(
        self,
        original_filename: str,
        stored_filename: str,
        file_type: str,
        file_size: int,
        content_hash: str,
        storage_path: str,
        mime_type: Optional[str] = None,
        file_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Inserts a new managed file record into metadata storage."""
        file_id = file_id or str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO files (id, original_filename, stored_filename, file_type, file_size, content_hash, mime_type, storage_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (file_id, original_filename, stored_filename, file_type, file_size, content_hash, mime_type, storage_path, created_at),
            )
            conn.commit()

        return self.get_file(file_id)  # type: ignore

    def get_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a managed file record by its ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_file_by_hash(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieves a managed file record by its SHA-256 hash."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files WHERE content_hash = ?", (content_hash,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_files(self) -> List[Dict[str, Any]]:
        """Lists all managed file records in the metadata database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def delete_file(self, file_id: str) -> bool:
        """Deletes a managed file record from the metadata database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
            conn.commit()
            return cursor.rowcount > 0

    # -------------------------------------------------------------
    # Agent Runs
    # -------------------------------------------------------------
    def create_agent_run(
        self,
        task: str,
        model_used: Optional[str] = None,
        status: str = "running",
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Creates a new agent run record."""
        run_id = run_id or str(uuid.uuid4())
        started_at = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO agent_runs (id, task, model_used, status, started_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, task, model_used, status, started_at),
            )
            conn.commit()

        return self.get_agent_run(run_id)  # type: ignore

    def update_agent_run(
        self,
        run_id: str,
        status: str,
        completed_at: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Updates the status and optional completion timestamp of an agent run."""
        completed_at = completed_at or (
            datetime.now(timezone.utc).isoformat() if status in ("completed", "error", "max_iterations_reached") else None
        )

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE agent_runs
                SET status = ?, completed_at = ?
                WHERE id = ?
                """,
                (status, completed_at, run_id),
            )
            conn.commit()

        return self.get_agent_run(run_id)

    def get_agent_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves an agent run by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agent_runs WHERE id = ?", (run_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_agent_runs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Lists recent agent runs."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agent_runs ORDER BY started_at DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # -------------------------------------------------------------
    # Agent Steps
    # -------------------------------------------------------------
    def record_agent_step(
        self,
        run_id: str,
        iteration: int,
        tool: str,
        arguments: Any,
        result: Any,
        status: str,
        step_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Records an execution step within an agent run."""
        step_id = step_id or str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        args_str = json.dumps(arguments) if not isinstance(arguments, str) else arguments
        res_str = str(result) if not isinstance(result, str) else result

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO agent_steps (id, run_id, iteration, tool, arguments, result, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (step_id, run_id, iteration, tool, args_str, res_str, status, created_at),
            )
            conn.commit()

        return {
            "id": step_id,
            "run_id": run_id,
            "iteration": iteration,
            "tool": tool,
            "arguments": args_str,
            "result": res_str,
            "status": status,
            "created_at": created_at,
        }

    def get_agent_steps(self, run_id: str) -> List[Dict[str, Any]]:
        """Retrieves all steps executed for a given agent run."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM agent_steps WHERE run_id = ? ORDER BY iteration ASC, created_at ASC",
                (run_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    # -------------------------------------------------------------
    # Audit Logs
    # -------------------------------------------------------------
    def log_audit_event(
        self,
        event: str,
        component: str,
        details: Any = None,
        log_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Records an immutable security/operational audit log entry."""
        log_id = log_id or str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        details_str = json.dumps(details) if isinstance(details, (dict, list)) else (str(details) if details is not None else None)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_logs (id, timestamp, event, component, details)
                VALUES (?, ?, ?, ?, ?)
                """,
                (log_id, timestamp, event, component, details_str),
            )
            conn.commit()

        return {
            "id": log_id,
            "timestamp": timestamp,
            "event": event,
            "component": component,
            "details": details_str,
        }

    def get_audit_logs(
        self,
        limit: int = 100,
        component: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves audit log entries, optionally filtered by component."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if component:
                cursor.execute(
                    "SELECT * FROM audit_logs WHERE component = ? ORDER BY timestamp DESC LIMIT ?",
                    (component, limit),
                )
            else:
                cursor.execute(
                    "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?",
                    (limit,),
                )
            return [dict(row) for row in cursor.fetchall()]
