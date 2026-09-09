"""
SOAR Backend API Layer.
Provides FastAPI REST API endpoints for tasks, execution events, file storage, and model metadata.
"""

from .app import create_app
from .dependencies import (
    get_app_config,
    get_db_manager,
    get_event_emitter,
    get_model_manager,
    get_orchestrator,
    get_storage,
    reset_api_dependencies,
    set_api_dependencies,
)
from .schemas import (
    ErrorResponse,
    EventItem,
    FileDeleteResponse,
    FileListResponse,
    FileMetadataResponse,
    HealthResponse,
    ModelItem,
    ModelListResponse,
    TaskEventsResponse,
    TaskRequest,
    TaskResponse,
)

__all__ = [
    "create_app",
    "get_app_config",
    "get_orchestrator",
    "get_storage",
    "get_db_manager",
    "get_model_manager",
    "get_event_emitter",
    "set_api_dependencies",
    "reset_api_dependencies",
    "HealthResponse",
    "TaskRequest",
    "TaskResponse",
    "EventItem",
    "TaskEventsResponse",
    "FileMetadataResponse",
    "FileListResponse",
    "FileDeleteResponse",
    "ModelItem",
    "ModelListResponse",
    "ErrorResponse",
]
