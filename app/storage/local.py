import hashlib
import json
import logging
import mimetypes
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional

from app.database.repository import DatabaseManager

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

logger = logging.getLogger(__name__)

# Reserved device names in Windows (case-insensitive)
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}

SAFE_FILE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+$")


class LocalFileStorage(BaseFileStorage):
    """
    Local filesystem storage engine for SOAR.
    Provides secure upload, download, metadata tracking, and deletion
    with strict path traversal defense and file size enforcement.
    """

    DEFAULT_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB default limit

    def __init__(
        self,
        storage_dir: str | Path = "data/files",
        max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE,
        allow_empty: bool = True,
        db_manager: Optional[DatabaseManager] = None,
    ):
        self.storage_dir = Path(storage_dir).resolve()
        self.meta_dir = self.storage_dir / ".meta"
        self.max_file_size_bytes = max_file_size_bytes
        self.allow_empty = allow_empty
        self.db_manager = db_manager

        # Ensure storage and metadata directories exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------
    # Security & Sanitization Helpers
    # -------------------------------------------------------------
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitizes an original user filename to neutralize path traversal,
        null bytes, control characters, and Windows reserved device names.
        """
        if not filename or not isinstance(filename, str):
            raise InvalidFilenameError("Filename must be a non-empty string.")

        # Check and reject null bytes
        if "\0" in filename:
            raise InvalidFilenameError("Filename contains prohibited null bytes.")

        # Strip any directory navigation components
        clean_name = os.path.basename(filename.replace("\\", "/"))
        clean_name = clean_name.strip()

        # Remove leading/trailing dots and whitespace
        clean_name = re.sub(r"^[\.\s]+|[\.\s]+$", "", clean_name)

        if not clean_name:
            clean_name = "unnamed_file"

        # Check for Windows reserved device names
        base_stem = Path(clean_name).stem.upper()
        if base_stem in WINDOWS_RESERVED_NAMES:
            clean_name = f"safe_{clean_name}"

        # Limit maximum length to 255 characters
        if len(clean_name) > 255:
            ext = Path(clean_name).suffix
            stem = Path(clean_name).stem[: 255 - len(ext)]
            clean_name = f"{stem}{ext}"

        return clean_name

    def _validate_file_id(self, file_id: str) -> str:
        """
        Validates that a file_id is a valid, safe identifier without
        path traversal characters or directory separators.
        """
        if not file_id or not isinstance(file_id, str):
            raise InvalidFilenameError("File ID must be a non-empty string.")

        file_id = file_id.strip()
        if not SAFE_FILE_ID_PATTERN.match(file_id):
            raise PathTraversalError(f"Invalid or unsafe file_id format: '{file_id}'")

        return file_id

    def _validate_containment(self, target_path: Path) -> Path:
        """
        Ensures target_path resolves strictly within the managed storage_dir root.
        Protects against symlink escapes and directory traversal.
        """
        resolved_target = target_path.resolve()
        resolved_root = self.storage_dir.resolve()

        try:
            resolved_target.relative_to(resolved_root)
        except ValueError:
            raise PathTraversalError(
                f"Path traversal detected: target path '{resolved_target}' escapes storage root '{resolved_root}'"
            )

        return resolved_target

    # -------------------------------------------------------------
    # Metadata Persistence Helpers
    # -------------------------------------------------------------
    def _save_meta_record(self, meta: StoredFileMetadata) -> None:
        """Persists metadata to local json file and optionally to SQLite."""
        meta_file = self.meta_dir / f"{meta.file_id}.json"
        self._validate_containment(meta_file)
        meta_file.write_text(json.dumps(meta.to_dict(), indent=2), encoding="utf-8")

        if self.db_manager:
            try:
                self.db_manager.insert_file(
                    original_filename=meta.original_filename,
                    stored_filename=meta.stored_filename,
                    file_type=meta.extension,
                    file_size=meta.size_bytes,
                    content_hash=meta.sha256,
                    storage_path=meta.storage_path,
                    mime_type=meta.mime_type,
                    file_id=meta.file_id,
                )
            except Exception as e:
                logger.warning(f"Failed to record file metadata in SQLite: {e}")

    def _delete_meta_record(self, file_id: str) -> None:
        """Deletes metadata from local json and optionally SQLite."""
        meta_file = self.meta_dir / f"{file_id}.json"
        if meta_file.exists():
            try:
                self._validate_containment(meta_file)
                meta_file.unlink()
            except Exception as e:
                logger.warning(f"Error removing metadata file '{meta_file}': {e}")

        if self.db_manager:
            try:
                self.db_manager.delete_file(file_id)
            except Exception as e:
                logger.warning(f"Error deleting file from SQLite: {e}")

    # -------------------------------------------------------------
    # Core BaseFileStorage Implementation
    # -------------------------------------------------------------
    def save(
        self,
        content: bytes | BinaryIO | str | Path,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> StoredFileMetadata:
        """
        Stores a file and returns its managed metadata.
        Accepts raw bytes, a readable binary stream, or a local file path.
        """
        # 1. Resolve raw content, original filename, and size
        if isinstance(content, (str, Path)):
            src_path = Path(content).resolve()
            if not src_path.exists():
                raise FileNotFoundStorageError(f"Source file not found at '{src_path}'")
            if src_path.is_dir():
                raise InvalidFileError(f"Source path '{src_path}' is a directory, not a file.")

            file_size = src_path.stat().st_size
            if file_size > self.max_file_size_bytes:
                raise FileTooLargeError(
                    f"File size ({file_size} bytes) exceeds maximum limit of {self.max_file_size_bytes} bytes."
                )
            if not self.allow_empty and file_size == 0:
                raise InvalidFileError("Empty files are not allowed by storage policy.")

            raw_bytes = src_path.read_bytes()
            orig_name = filename or src_path.name

        elif isinstance(content, bytes):
            file_size = len(content)
            if file_size > self.max_file_size_bytes:
                raise FileTooLargeError(
                    f"File size ({file_size} bytes) exceeds maximum limit of {self.max_file_size_bytes} bytes."
                )
            if not self.allow_empty and file_size == 0:
                raise InvalidFileError("Empty files are not allowed by storage policy.")

            raw_bytes = content
            orig_name = filename or "upload.bin"

        elif hasattr(content, "read"):
            # Stream-like object
            chunks: List[bytes] = []
            total_size = 0
            while True:
                chunk = content.read(65536)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > self.max_file_size_bytes:
                    raise FileTooLargeError(
                        f"Stream size exceeded maximum allowed limit of {self.max_file_size_bytes} bytes."
                    )
                chunks.append(chunk)

            raw_bytes = b"".join(chunks)
            file_size = len(raw_bytes)
            if not self.allow_empty and file_size == 0:
                raise InvalidFileError("Empty files are not allowed by storage policy.")

            orig_name = filename or "upload.bin"
        else:
            raise InvalidFileError(f"Unsupported content type: {type(content)}")

        # 2. Sanitize original filename
        safe_orig_name = self._sanitize_filename(orig_name)
        extension = Path(safe_orig_name).suffix.lower()

        # 3. Calculate SHA-256
        sha256_hash = hashlib.sha256(raw_bytes).hexdigest()

        # 4. Guess or resolve MIME type
        detected_mime = content_type or mimetypes.guess_type(safe_orig_name)[0] or "application/octet-stream"

        # 5. Generate unique file_id and safe destination path
        file_id = str(uuid.uuid4())
        stored_filename = f"{file_id}{extension}"
        dest_path = self.storage_dir / stored_filename
        self._validate_containment(dest_path)

        # 6. Write file to disk
        dest_path.write_bytes(raw_bytes)

        # 7. Construct metadata
        created_at = datetime.now(timezone.utc).isoformat()
        metadata = StoredFileMetadata(
            file_id=file_id,
            original_filename=safe_orig_name,
            stored_filename=stored_filename,
            extension=extension,
            size_bytes=file_size,
            sha256=sha256_hash,
            storage_path=str(dest_path.resolve()),
            created_at=created_at,
            mime_type=detected_mime,
        )

        # 8. Persist metadata
        self._save_meta_record(metadata)

        return metadata

    def get_path(self, file_id: str) -> Path:
        """
        Resolves the local storage path for a given file_id.
        Ensures the path is valid and strictly contained in storage_dir.
        """
        safe_id = self._validate_file_id(file_id)
        meta = self.get_metadata(safe_id)
        if not meta:
            raise FileNotFoundStorageError(f"File with ID '{file_id}' not found.")

        target_path = Path(meta.storage_path)
        self._validate_containment(target_path)

        if not target_path.exists():
            raise FileNotFoundStorageError(f"Stored file for ID '{file_id}' not found on disk at '{target_path}'.")

        return target_path

    def get_bytes(self, file_id: str) -> bytes:
        """Reads and returns the complete binary content of a managed file."""
        target_path = self.get_path(file_id)
        return target_path.read_bytes()

    def get_stream(self, file_id: str) -> BinaryIO:
        """Opens and returns a readable binary stream for a managed file."""
        target_path = self.get_path(file_id)
        return open(target_path, "rb")

    def get_metadata(self, file_id: str) -> Optional[StoredFileMetadata]:
        """Retrieves metadata for a managed file."""
        try:
            safe_id = self._validate_file_id(file_id)
        except (InvalidFilenameError, PathTraversalError):
            return None

        # Try SQLite first if db_manager is active
        if self.db_manager:
            try:
                row = self.db_manager.get_file(safe_id)
                if row:
                    return StoredFileMetadata(
                        file_id=row["id"],
                        original_filename=row["original_filename"],
                        stored_filename=row["stored_filename"],
                        extension=row["file_type"],
                        size_bytes=row["file_size"],
                        sha256=row["content_hash"],
                        storage_path=row["storage_path"],
                        created_at=row["created_at"],
                        mime_type=row.get("mime_type"),
                    )
            except Exception as e:
                logger.debug(f"SQLite metadata lookup fallback to disk: {e}")

        # Fallback to local json metadata file
        meta_file = self.meta_dir / f"{safe_id}.json"
        if meta_file.exists():
            try:
                self._validate_containment(meta_file)
                data = json.loads(meta_file.read_text(encoding="utf-8"))
                return StoredFileMetadata.from_dict(data)
            except Exception as e:
                logger.warning(f"Failed to read metadata file '{meta_file}': {e}")

        # If metadata record doesn't exist, check if a matching file exists on disk
        for disk_file in self.storage_dir.glob(f"{safe_id}.*"):
            if disk_file.is_file():
                try:
                    self._validate_containment(disk_file)
                    stat = disk_file.stat()
                    ext = disk_file.suffix.lower()
                    return StoredFileMetadata(
                        file_id=safe_id,
                        original_filename=disk_file.name,
                        stored_filename=disk_file.name,
                        extension=ext,
                        size_bytes=stat.st_size,
                        sha256=hashlib.sha256(disk_file.read_bytes()).hexdigest(),
                        storage_path=str(disk_file.resolve()),
                        created_at=datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
                        mime_type=mimetypes.guess_type(disk_file.name)[0] or "application/octet-stream",
                    )
                except Exception:
                    pass

        return None

    def exists(self, file_id: str) -> bool:
        """Checks if a file with the given file_id exists in storage."""
        try:
            safe_id = self._validate_file_id(file_id)
            meta = self.get_metadata(safe_id)
            if not meta:
                return False
            target_path = Path(meta.storage_path)
            self._validate_containment(target_path)
            return target_path.exists()
        except Exception:
            return False

    def delete(self, file_id: str) -> bool:
        """
        Deletes a managed file and its metadata.
        Returns True if deleted successfully, False if file was not found.
        """
        try:
            safe_id = self._validate_file_id(file_id)
        except (InvalidFilenameError, PathTraversalError):
            return False

        meta = self.get_metadata(safe_id)
        if not meta:
            return False

        target_path = Path(meta.storage_path)
        try:
            self._validate_containment(target_path)
        except PathTraversalError:
            return False

        deleted = False
        if target_path.exists():
            target_path.unlink()
            deleted = True

        self._delete_meta_record(safe_id)
        return deleted or True

    def list_files(self) -> List[StoredFileMetadata]:
        """Returns a list of metadata for all managed files."""
        # If db_manager is available, retrieve from database
        if self.db_manager:
            try:
                db_files = self.db_manager.list_files()
                result = []
                for row in db_files:
                    result.append(
                        StoredFileMetadata(
                            file_id=row["id"],
                            original_filename=row["original_filename"],
                            stored_filename=row["stored_filename"],
                            extension=row["file_type"],
                            size_bytes=row["file_size"],
                            sha256=row["content_hash"],
                            storage_path=row["storage_path"],
                            created_at=row["created_at"],
                            mime_type=row.get("mime_type"),
                        )
                    )
                return result
            except Exception as e:
                logger.warning(f"Error querying list_files from database: {e}")

        # Otherwise read from meta directory
        result = []
        for meta_file in self.meta_dir.glob("*.json"):
            try:
                self._validate_containment(meta_file)
                data = json.loads(meta_file.read_text(encoding="utf-8"))
                result.append(StoredFileMetadata.from_dict(data))
            except Exception:
                pass

        return sorted(result, key=lambda m: m.created_at, reverse=True)
