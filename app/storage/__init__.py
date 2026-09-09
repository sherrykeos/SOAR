"""
SOAR Local File Storage Subsystem.
Provides clean, secure, local file upload, download, metadata indexing, and deletion.
"""

from .base import (
    BaseFileStorage,
    FileNotFoundStorageError,
    FileTooLargeError,
    InvalidFileError,
    InvalidFilenameError,
    PathTraversalError,
    StorageError,
    StoredFileMetadata,
)
from .local import LocalFileStorage

__all__ = [
    "BaseFileStorage",
    "LocalFileStorage",
    "StoredFileMetadata",
    "StorageError",
    "FileNotFoundStorageError",
    "PathTraversalError",
    "FileTooLargeError",
    "InvalidFilenameError",
    "InvalidFileError",
]
