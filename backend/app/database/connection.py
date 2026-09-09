import sqlite3
from pathlib import Path
from typing import Generator
import contextlib


DEFAULT_DB_PATH = Path("data/soar.db")


def get_connection(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """
    Creates and configures an SQLite connection with WAL mode and foreign keys enabled.
    Ensures the parent directory exists.
    """
    path = Path(db_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


@contextlib.contextmanager
def get_db_connection(db_path: str | Path = DEFAULT_DB_PATH) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager yielding an SQLite connection and ensuring it is properly closed.
    """
    conn = get_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


@contextlib.contextmanager
def get_db_cursor(db_path: str | Path = DEFAULT_DB_PATH) -> Generator[sqlite3.Cursor, None, None]:
    """
    Context manager providing a database cursor and automatically committing on success
    or rolling back on exception, closing connection on completion.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
