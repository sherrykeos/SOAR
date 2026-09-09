from fastapi import APIRouter

from .files import router as files_router
from .health import router as health_router
from .models import router as models_router
from .tasks import router as tasks_router

api_router = APIRouter(prefix="/api")

api_router.include_router(health_router)
api_router.include_router(tasks_router)
api_router.include_router(files_router)
api_router.include_router(models_router)

__all__ = ["api_router"]
