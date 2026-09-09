import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.api.dependencies import get_storage
from app.api.schemas import (
    FileDeleteResponse,
    FileListResponse,
    FileMetadataResponse,
)
from app.storage import (
    FileNotFoundStorageError,
    FileTooLargeError,
    InvalidFileError,
    InvalidFilenameError,
    LocalFileStorage,
    PathTraversalError,
    StorageError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload", response_model=FileMetadataResponse, status_code=status.HTTP_201_CREATED)
def upload_file(
    file: UploadFile = File(...),
    storage: LocalFileStorage = Depends(get_storage),
) -> FileMetadataResponse:
    """
    Uploads and safely stores a local file in SOAR's managed storage.
    Enforces path traversal protection, filename sanitization, and size limits.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename.",
        )

    try:
        meta = storage.save(
            content=file.file,
            filename=file.filename,
            content_type=file.content_type,
        )

        return FileMetadataResponse(
            file_id=meta.file_id,
            original_filename=meta.original_filename,
            size_bytes=meta.size_bytes,
            mime_type=meta.mime_type,
            sha256=meta.sha256,
            created_at=meta.created_at,
        )

    except FileTooLargeError as e:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(e),
        )
    except (InvalidFilenameError, InvalidFileError, PathTraversalError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Unexpected error during file upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}",
        )


@router.get("", response_model=FileListResponse)
def list_files(
    limit: int = Query(50, ge=1, le=500, description="Maximum number of files to return."),
    offset: int = Query(0, ge=0, description="Number of files to skip for pagination."),
    storage: LocalFileStorage = Depends(get_storage),
) -> FileListResponse:
    """
    Lists all managed files in SOAR storage with optional pagination.
    """
    all_files = storage.list_files()
    total_count = len(all_files)
    paginated_files = all_files[offset : offset + limit]

    file_items = [
        FileMetadataResponse(
            file_id=f.file_id,
            original_filename=f.original_filename,
            size_bytes=f.size_bytes,
            mime_type=f.mime_type,
            sha256=f.sha256,
            created_at=f.created_at,
        )
        for f in paginated_files
    ]

    return FileListResponse(
        total=total_count,
        files=file_items,
    )


@router.get("/{file_id}", response_model=FileMetadataResponse)
def get_file_metadata(
    file_id: str,
    storage: LocalFileStorage = Depends(get_storage),
) -> FileMetadataResponse:
    """
    Retrieves metadata for a specific managed file by file_id.
    """
    meta = storage.get_metadata(file_id)
    if not meta or not storage.exists(file_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The requested file with ID '{file_id}' does not exist.",
        )

    return FileMetadataResponse(
        file_id=meta.file_id,
        original_filename=meta.original_filename,
        size_bytes=meta.size_bytes,
        mime_type=meta.mime_type,
        sha256=meta.sha256,
        created_at=meta.created_at,
    )


@router.get("/{file_id}/download")
def download_file(
    file_id: str,
    storage: LocalFileStorage = Depends(get_storage),
):
    """
    Downloads the binary content of a managed file by file_id.
    Protected against path traversal and arbitrary filesystem escape.
    """
    try:
        path = storage.get_path(file_id)
        meta = storage.get_metadata(file_id)
        download_name = meta.original_filename if meta else path.name
        media_type = meta.mime_type if meta else "application/octet-stream"

        return FileResponse(
            path=str(path),
            filename=download_name,
            media_type=media_type,
        )

    except FileNotFoundStorageError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The requested file with ID '{file_id}' does not exist.",
        )
    except (PathTraversalError, InvalidFilenameError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file request: {str(e)}",
        )
    except Exception as e:
        logger.exception(f"Error downloading file '{file_id}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve file: {str(e)}",
        )


@router.delete("/{file_id}", response_model=FileDeleteResponse)
def delete_file(
    file_id: str,
    storage: LocalFileStorage = Depends(get_storage),
) -> FileDeleteResponse:
    """
    Deletes a managed file and its associated metadata by file_id.
    """
    if not storage.exists(file_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The requested file with ID '{file_id}' does not exist.",
        )

    deleted = storage.delete(file_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not delete file with ID '{file_id}'.",
        )

    return FileDeleteResponse(
        status="deleted",
        file_id=file_id,
    )
