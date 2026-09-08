"""
Database package for SOAR.
Provides SQLite metadata storage, connection management, schema creation, and repository methods.
"""

from .connection import DEFAULT_DB_PATH, get_connection, get_db_cursor
from .repository import DatabaseManager
from .schema import create_tables

__all__ = [
    "DEFAULT_DB_PATH",
    "get_connection",
    "get_db_cursor",
    "DatabaseManager",
    "create_tables",
]
