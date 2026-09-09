from fastapi import APIRouter
from app.api.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Returns application health and operational status."""
    return HealthResponse(
        status="ok",
        app="SOAR",
        version="0.1.0",
    )
