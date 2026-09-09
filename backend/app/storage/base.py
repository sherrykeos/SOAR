from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional


class StorageError(Exception):
    """Base exception for all storage-related errors."""
    pass


class FileNotFoundStorageError(StorageError):
    """Raised when a requested file ID or path is not found."""
    pass


class PathTraversalError(StorageError):
    """Raised when a path traversal or unauthorized filesystem escape is detected."""
    pass


class FileTooLargeError(StorageError):
    """Raised when a file exceeds the configured maximum allowed size."""
    pass


class InvalidFilenameError(StorageError):
    """Raised when a filename is invalid or violates security constraints."""
    pass


class InvalidFileError(StorageError):
    """Raised when a file input or structure is invalid."""
    pass


@dataclass
class StoredFileMetadata:
    """Metadata representing a managed stored file in SOAR."""
    file_id: str
    original_filename: str
    stored_filename: str
    extension: str
    size_bytes: int
    sha256: str
    storage_path: str
    created_at: str
    mime_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converts metadata to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StoredFileMetadata":
        """Reconstructs metadata from a dictionary."""
        return cls(
            file_id=data["file_id"],
            original_filename=data["original_filename"],
            stored_filename=data["stored_filename"],
            extension=data["extension"],
            size_bytes=int(data["size_bytes"]),
            sha256=data["sha256"],
            storage_path=data["storage_path"],
            created_at=data["created_at"],
            mime_type=data.get("mime_type"),
        )


class BaseFileStorage(ABC):
    """
    Abstract Base Class for SOAR file storage backends.
    Decouples storage management from API/HTTP layers and the agent core.
    """

    @abstractmethod
    def save(
        self,
        content: bytes | BinaryIO | str | Path,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> StoredFileMetadata:
        """
        Stores a file and returns its managed metadata.

        Args:
            content: Raw bytes, an open binary stream, or a local file path / Path object.
            filename: Original user filename (required if content is bytes or stream).
            content_type: Optional MIME type override.

        Returns:
            StoredFileMetadata with file_id, sha256, path, size, etc.
        """
        pass

    @abstractmethod
    def get_path(self, file_id: str) -> Path:
        """
        Resolves the local storage path for a given file_id.

        Args:
            file_id: Unique identifier for the file.

        Returns:
            Path object pointing to the stored file.

        Raises:
            FileNotFoundStorageError: If file does not exist.
            PathTraversalError: If path resolution escapes storage root.
        """
        pass

    @abstractmethod
    def get_bytes(self, file_id: str) -> bytes:
        """
        Reads and returns the complete binary content of a managed file.

        Args:
            file_id: Unique identifier for the file.

        Returns:
            Raw bytes of the file.
        """
        pass

    @abstractmethod
    def get_stream(self, file_id: str) -> BinaryIO:
        """
        Opens and returns a readable binary stream for a managed file.

        Args:
            file_id: Unique identifier for the file.

        Returns:
            Open BinaryIO stream in 'rb' mode.
        """
        pass

    @abstractmethod
    def get_metadata(self, file_id: str) -> Optional[StoredFileMetadata]:
        """
        Retrieves metadata for a managed file.

        Args:
            file_id: Unique identifier for the file.

        Returns:
            StoredFileMetadata if found, else None.
        """
        pass

    @abstractmethod
    def exists(self, file_id: str) -> bool:
        """Checks if a file with the given file_id exists in storage."""
        pass

    @abstractmethod
    def delete(self, file_id: str) -> bool:
        """
        Deletes a managed file and its metadata.

        Args:
            file_id: Unique identifier for the file.

        Returns:
            True if deleted successfully, False if file was not found.
        """
        pass

    @abstractmethod
    def list_files(self) -> List[StoredFileMetadata]:
        """Returns a list of metadata for all managed files."""
        pass
