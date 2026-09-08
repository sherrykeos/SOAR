import sqlite3


DOCUMENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    source_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

AGENT_RUNS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS agent_runs (
    id TEXT PRIMARY KEY,
    task TEXT NOT NULL,
    model_used TEXT,
    status TEXT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
"""

AGENT_STEPS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS agent_steps (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    iteration INTEGER NOT NULL,
    tool TEXT NOT NULL,
    arguments TEXT,
    result TEXT,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

AUDIT_LOGS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event TEXT NOT NULL,
    component TEXT NOT NULL,
    details TEXT
);
"""

INDEXES_SQL = """
CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash);
CREATE INDEX IF NOT EXISTS idx_agent_steps_run_id ON agent_steps(run_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
"""


def create_tables(conn: sqlite3.Connection) -> None:
    """Initializes all foundational database tables and indexes."""
    cursor = conn.cursor()
    cursor.execute(DOCUMENTS_TABLE_SQL)
    cursor.execute(AGENT_RUNS_TABLE_SQL)
    cursor.execute(AGENT_STEPS_TABLE_SQL)
    cursor.execute(AUDIT_LOGS_TABLE_SQL)
    cursor.executescript(INDEXES_SQL)
    conn.commit()
