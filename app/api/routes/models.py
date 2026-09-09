from typing import List
from fastapi import APIRouter, Depends

from app.api.dependencies import get_app_config, get_model_manager
from app.api.schemas import ModelItem, ModelListResponse
from app.config import SOARConfig
from app.models.manager import ModelManager

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("", response_model=ModelListResponse)
def list_models(
    config: SOARConfig = Depends(get_app_config),
    manager: ModelManager = Depends(get_model_manager),
) -> ModelListResponse:
    """
    Returns currently configured local models and their local availability status.
    Reflects configuration from config/config.yaml without hardcoded models.
    """
    items: List[ModelItem] = []

    # Map registered adapters by model_id for fast availability check
    registered_models = {m.model_id: m for m in manager.registry.list_models()}

    for model_cfg in config.models:
        adapter = registered_models.get(model_cfg.id)
        is_avail = adapter.is_available() if adapter else False

        items.append(
            ModelItem(
                id=model_cfg.id,
                provider=model_cfg.provider,
                capabilities=list(model_cfg.capabilities),
                priority=model_cfg.priority,
                enabled=model_cfg.enabled,
                available=is_avail,
                timeout=model_cfg.timeout,
            )
        )

    # Fallback if config.models was empty: inspect registry directly
    if not items:
        for m in manager.registry.list_models():
            items.append(
                ModelItem(
                    id=m.model_id,
                    provider=m.provider,
                    capabilities=list(m.capabilities),
                    priority=m.priority,
                    enabled=True,
                    available=m.is_available(),
                    timeout=getattr(m, "timeout", None),
                )
            )

    return ModelListResponse(
        default_model=config.agent.default_model_id,
        models=items,
    )
