from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from .adapter import ModelAdapter, ModelCapability
from .registry import ModelRegistry


@dataclass
class ModelRouteDecision:
    """
    Structured outcome of the adaptive model routing decision.
    """

    requested_model_id: str
    selected_model: ModelAdapter
    fallback_model_id: str
    timeout_seconds: float = 180.0
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
    task_profile: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requested_model_id": self.requested_model_id,
            "selected_model_id": self.selected_model.model_id,
            "fallback_model_id": self.fallback_model_id,
            "timeout_seconds": self.timeout_seconds,
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
            "task_profile": self.task_profile.to_dict() if hasattr(self.task_profile, "to_dict") else self.task_profile,
        }


class ModelRouter:

    def __init__(
        self,
        registry: ModelRegistry,
        default_model_id: str = "qwen3:1.7b",
        hard_model_timeout: float = 15.0,
    ):
        self.registry = registry
        self.default_model_id = default_model_id
        self.hard_model_timeout = hard_model_timeout

    def route(self, task_type: str = ModelCapability.GENERAL) -> ModelAdapter:
        """
        Selects the best available model for the given task_type / capability.
        Raises ValueError if no registered model supports the capability.
        """
        candidates = self.registry.find_by_capability(task_type)
        if candidates:
            return candidates[0]

        raise ValueError(
            f"No registered model supports capability '{task_type}'. "
            f"Available models: {[m.model_id for m in self.registry.list_models()]}"
        )

    def route_by_id(self, model_id: str) -> ModelAdapter:
        """Retrieves a specific model by model_id."""
        return self.registry.get(model_id)

    def route_task(
        self,
        profile: Any,
        fallback_model_id: Optional[str] = None,
    ) -> ModelRouteDecision:
        """
        Routes a structured TaskProfile to the optimal local model.
        Checks model availability and automatically routes to a local fallback if needed.
        Speed > Accuracy priority for MVP.
        """
        fallback_id = fallback_model_id or self.default_model_id
        timeout_sec = 180.0

        # 1. Determine requested target model ID based on task profile
        if getattr(profile, "requires_coding", False):
            requested_model_id = "qwen2.5-coder:1.5b"
            target_capability = ModelCapability.CODING
        elif getattr(profile, "requires_vision", False):
            requested_model_id = "qwen2.5vl:3b"
            target_capability = ModelCapability.VISION
        elif getattr(profile, "complexity", "simple") == "hard":
            requested_model_id = "qwen2:4b"
            target_capability = ModelCapability.REASONING
            timeout_sec = self.hard_model_timeout
        else:
            # Simple / medium reasoning, calculation, direct Q&A -> fast model
            requested_model_id = "qwen3:1.7b"
            target_capability = ModelCapability.GENERAL

        # 2. Check if requested model exists in registry and is available locally
        candidate_model: Optional[ModelAdapter] = None
        try:
            candidate = self.registry.get(requested_model_id)
            if candidate.is_available():
                candidate_model = candidate
        except KeyError:
            # If not found by exact ID, check by capability
            capability_matches = self.registry.find_by_capability(target_capability)
            for m in capability_matches:
                if m.is_available():
                    candidate_model = m
                    break

        if candidate_model is not None:
            return ModelRouteDecision(
                requested_model_id=requested_model_id,
                selected_model=candidate_model,
                fallback_model_id=fallback_id,
                timeout_seconds=timeout_sec,
                fallback_used=False,
                fallback_reason=None,
                task_profile=profile,
            )

        # 3. Model is unavailable -> Fall back to default local model (qwen3:1.7b or first available general model)
        fallback_model: Optional[ModelAdapter] = None
        try:
            fb = self.registry.get(fallback_id)
            if fb.is_available():
                fallback_model = fb
        except KeyError:
            pass

        if fallback_model is None:
            # Find any available general model
            general_models = self.registry.find_by_capability(ModelCapability.GENERAL)
            for m in general_models:
                if m.is_available():
                    fallback_model = m
                    break
            if fallback_model is None and general_models:
                fallback_model = general_models[0]

        if fallback_model is None:
            all_models = self.registry.list_models()
            if all_models:
                fallback_model = all_models[0]
            else:
                raise ValueError("No local models available in registry.")

        return ModelRouteDecision(
            requested_model_id=requested_model_id,
            selected_model=fallback_model,
            fallback_model_id=fallback_id,
            timeout_seconds=180.0,
            fallback_used=True,
            fallback_reason="requested model unavailable",
            task_profile=profile,
        )
