from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ------------------------------------------------------------------------------
# Health Schemas
# ------------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str = "ok"
    app: str = "SOAR"
    version: str = "0.1.0"


# ------------------------------------------------------------------------------
# Task & Event Schemas
# ------------------------------------------------------------------------------
class TaskRequest(BaseModel):
    task: str = Field(..., min_length=1, description="The user prompt or task description to execute.")
    model: Optional[str] = Field(None, description="Optional explicit model ID override. None implies auto-routing.")


class TaskModelInfo(BaseModel):
    requested: Optional[str] = None
    actual: Optional[str] = None
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
    duration_seconds: Optional[float] = 0.0


class TaskResponse(BaseModel):
    run_id: str
    status: str
    answer: str
    model: str
    execution_mode: str
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    model_details: Optional[Dict[str, Any]] = None
    events: List[Dict[str, Any]] = Field(default_factory=list)


class EventItem(BaseModel):
    event_id: str
    run_id: Optional[str] = None
    stage: str
    status: str
    message: str
    timestamp: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskEventsResponse(BaseModel):
    run_id: str
    events: List[EventItem]


# ------------------------------------------------------------------------------
# File Schemas
# ------------------------------------------------------------------------------
class FileMetadataResponse(BaseModel):
    file_id: str
    original_filename: str
    size_bytes: int
    mime_type: Optional[str] = None
    sha256: str
    created_at: str


class FileListResponse(BaseModel):
    total: int
    files: List[FileMetadataResponse]


class FileDeleteResponse(BaseModel):
    status: str = "deleted"
    file_id: str


# ------------------------------------------------------------------------------
# Model Schemas
# ------------------------------------------------------------------------------
class ModelItem(BaseModel):
    id: str
    provider: str
    capabilities: List[str]
    priority: int
    enabled: bool
    available: bool = True
    timeout: Optional[float] = None


class ModelListResponse(BaseModel):
    default_model: str
    models: List[ModelItem]


# ------------------------------------------------------------------------------
# Error Schema
# ------------------------------------------------------------------------------
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Any] = None
