import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.exceptions import ResponseValidationError
from fastapi.responses import JSONResponse

from app.api.dependencies import get_orchestrator, set_api_dependencies
from app.api.routes import api_router
from app.api.schemas import ErrorResponse
from app.config import SOARConfig, get_config
from app.storage import StorageError

logger = logging.getLogger(__name__)


def create_app(config: Optional[SOARConfig] = None) -> FastAPI:
    """
    Application Factory for SOAR FastAPI REST API.
    Mounts core API routes, configures error handlers, and wires dependencies.
    """
    app_cfg = config or get_config()
    if config is not None:
        set_api_dependencies(config=config)

    app = FastAPI(
        title=app_cfg.app.name,
        description="Sovereign On-Premise Agentic AI Workbench REST API",
        version="0.1.0",
        docs_url="/docs" if app_cfg.app.debug or app_cfg.app.environment != "production" else None,
        redoc_url="/redoc" if app_cfg.app.debug or app_cfg.app.environment != "production" else None,
    )

    # -------------------------------------------------------------
    # Exception Handlers
    # -------------------------------------------------------------
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "http_error",
                "message": exc.detail,
                "details": None,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "validation_error",
                "message": "Invalid request payload format.",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(ResponseValidationError)
    async def response_validation_exception_handler(request: Request, exc: ResponseValidationError):
        logger.exception("Task response validation failed: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "response_validation_error",
                "message": "The task completed, but the API response could not be serialized.",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(StorageError)
    async def storage_exception_handler(request: Request, exc: StorageError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "storage_error",
                "message": str(exc),
                "details": None,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled server error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_error",
                "message": f"An unexpected error occurred during processing: {exc}",
                "details": None,
            },
        )

    # -------------------------------------------------------------
    # Mount Primary API Router
    # -------------------------------------------------------------
    app.include_router(api_router)

    # -------------------------------------------------------------
    # Root & Backwards-Compatibility Routes
    # -------------------------------------------------------------
    @app.get("/")
    def root():
        return {
            "name": app_cfg.app.name,
            "status": "online",
            "version": "0.1.0",
        }

    @app.get("/health")
    def legacy_health():
        return {
            "status": "healthy",
        }

    @app.post("/chat")
    def legacy_chat(request: dict):
        orch = get_orchestrator()
        task_text = str(request.get("task", ""))
        state = orch.run(task_text)
        return {
            "task": state.task,
            "status": state.status,
            "plan": state.plan,
            "results": state.results,
        }

    return app
