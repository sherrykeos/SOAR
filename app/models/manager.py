import logging
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from .adapter import ModelAdapter, ModelCapability
from .mock import MockModel
from .ollama import OllamaModel
from .registry import ModelRegistry
from .router import ModelRouteDecision, ModelRouter

logger = logging.getLogger(__name__)


@dataclass
class ModelExecutionResult:
    """
    Structured outcome of an LLM generation call, recording the actual model used,
    response, latency, and any fallback information.
    """

    response: str
    requested_model_id: str
    actual_model_id: str
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
    duration_seconds: float = 0.0
    task_profile: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response": self.response,
            "requested_model_id": self.requested_model_id,
            "actual_model_id": self.actual_model_id,
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
            "duration_seconds": self.duration_seconds,
            "task_profile": self.task_profile.to_dict() if hasattr(self.task_profile, "to_dict") else self.task_profile,
        }


class ModelManager:
    """
    Facade managing ModelRegistry and ModelRouter for SOAR on-premise execution.
    Provides plug-and-play local model routing, timeout safeguards, and local fallbacks.
    """

    def __init__(
        self,
        model_registry: ModelRegistry | None = None,
        model_router: ModelRouter | None = None,
        default_model_name: str = "qwen3:1.7b",
        hard_model_timeout: float = 15.0,
    ):
        self.default_model_name = default_model_name
        self.hard_model_timeout = hard_model_timeout

        if model_registry is None:
            self.registry = ModelRegistry()
            self._register_default_models(default_model_name)
        else:
            self.registry = model_registry

        self.router = model_router or ModelRouter(
            registry=self.registry,
            default_model_id=default_model_name,
            hard_model_timeout=hard_model_timeout,
        )

    def _register_default_models(self, default_model_name: str) -> None:
        """
        Registers SOAR's local model pool:
        1. qwen3:1.7b         - fast general, simple reasoning, fallback
        2. qwen2:4b           - hard reasoning, complex analysis
        3. qwen2.5-coder:1.5b - Python coding
        4. qwen2.5vl:3b       - vision / OCR / multimodal
        """
        # 1. Primary fast general model (default)
        self.registry.register(
            OllamaModel(
                model_name=default_model_name,
                capabilities={
                    ModelCapability.GENERAL,
                    ModelCapability.REASONING,
                },
                priority=10,
            )
        )

        # 2. Hard reasoning model
        self.registry.register(
            OllamaModel(
                model_name="qwen2:4b",
                capabilities={
                    ModelCapability.REASONING,
                },
                priority=20,
                timeout=self.hard_model_timeout,
            )
        )

        # 3. Python coding model
        self.registry.register(
            OllamaModel(
                model_name="qwen2.5-coder:1.5b",
                capabilities={
                    ModelCapability.CODING,
                },
                priority=15,
            )
        )

        # 4. Vision model
        self.registry.register(
            OllamaModel(
                model_name="qwen2.5vl:3b",
                capabilities={
                    ModelCapability.VISION,
                },
                priority=15,
            )
        )

        # 5. Backup mock coder for isolated unit tests
        self.registry.register(
            MockModel(
                model_id="mock-coder",
                capabilities={
                    ModelCapability.CODING,
                },
                priority=30,
                fixed_response="def solution():\n    return 'SOAR local coding response'",
            )
        )

    @property
    def model(self) -> ModelAdapter:
        """Backwards compatibility property returning the default general model."""
        return self.router.route(task_type=ModelCapability.GENERAL)

    def generate(
        self,
        prompt: str,
        *,
        task_type: str = ModelCapability.GENERAL,
        model_id: str | None = None,
        think: bool = False,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Routes the prompt to the appropriate model based on task_type or explicit model_id.
        """
        if model_id is not None:
            model = self.router.route_by_id(model_id)
        else:
            model = self.router.route(task_type=task_type)

        return model.generate(
            prompt,
            think=think,
            timeout=timeout,
            **kwargs,
        )

    def generate_with_routing(
        self,
        prompt: str,
        *,
        profile: Any = None,
        think: bool = False,
        timeout: float | None = None,
        emitter: Any = None,
        run_id: str | None = None,
        **kwargs: Any,
    ) -> ModelExecutionResult:
        """
        Executes text generation using adaptive routing based on TaskProfile.
        Includes automatic timeout safeguard (default 15s for 4B) and local fallback to qwen3:1.7b.
        Speed > Accuracy priority for MVP.
        """
        if profile is None:
            from app.orchestrator.task_classifier import TaskClassifier

            profile = TaskClassifier().classify(prompt)

        decision: ModelRouteDecision = self.router.route_task(profile)
        eff_timeout = timeout if timeout is not None else decision.timeout_seconds
        primary_model = decision.selected_model

        if decision.fallback_used and emitter:
            emitter.emit(
                stage="MODEL_SELECTING",
                status="IN_PROGRESS",
                message=f"Model {decision.requested_model_id} unavailable, falling back to {decision.selected_model.model_id}",
                metadata={
                    "requested_model": decision.requested_model_id,
                    "fallback_model": decision.selected_model.model_id,
                    "fallback_reason": decision.fallback_reason,
                },
                run_id=run_id,
            )

        if emitter:
            emitter.emit(
                stage="MODEL_SELECTING",
                status="COMPLETED",
                message=f"Model selected — {primary_model.model_id}",
                metadata={
                    "selected_model": primary_model.model_id,
                    "requested_model": decision.requested_model_id,
                    "fallback_used": decision.fallback_used,
                },
                run_id=run_id,
            )

        # 2. GENERATING_OUTPUT (Only after model selection has completed)
        output_label = "Python code" if (profile and getattr(profile, "execution_mode", "") == "code") else "response"
        if emitter:
            emitter.emit(
                stage="GENERATING_OUTPUT",
                status="STARTED",
                message=f"Generating {output_label}",
                metadata={"requires_rag": getattr(profile, "requires_rag", False) if profile else False},
                run_id=run_id,
            )

        start_time = time.perf_counter()

        # Try execution on selected model
        try:
            response = primary_model.generate(
                prompt,
                think=think,
                timeout=eff_timeout,
                **kwargs,
            )
            duration = time.perf_counter() - start_time
            if emitter:
                emitter.emit(
                    stage="GENERATING_OUTPUT",
                    status="COMPLETED",
                    message=f"{output_label.capitalize()} generated",
                    metadata={"duration_seconds": round(duration, 3)},
                    run_id=run_id,
                )
            return ModelExecutionResult(
                response=response,
                requested_model_id=decision.requested_model_id,
                actual_model_id=primary_model.model_id,
                fallback_used=decision.fallback_used,
                fallback_reason=decision.fallback_reason,
                duration_seconds=round(duration, 3),
                task_profile=profile,
            )
        except Exception as e:
            duration_failed = time.perf_counter() - start_time
            logger.warning(
                f"Model '{primary_model.model_id}' failed after {duration_failed:.2f}s: {e}. "
                f"Attempting fallback to '{decision.fallback_model_id}'."
            )

            # Determine fallback reason
            is_timeout = isinstance(e, TimeoutError) or "timed out" in str(e).lower()
            reason = "timeout" if is_timeout else f"inference error: {str(e)}"

            if emitter:
                emitter.emit(
                    stage="MODEL_SELECTING",
                    status="IN_PROGRESS",
                    message=f"Model timeout/unavailable, falling back to {decision.fallback_model_id}",
                    metadata={
                        "requested_model": decision.requested_model_id,
                        "fallback_model": decision.fallback_model_id,
                        "fallback_reason": reason,
                    },
                    run_id=run_id,
                )

            # If we were already on the fallback model and it crashed, re-raise
            if primary_model.model_id == decision.fallback_model_id:
                raise e

            # Fall back to local default model (qwen3:1.7b)
            try:
                fallback_model = self.router.route_by_id(decision.fallback_model_id)
            except Exception:
                fallback_model = self.router.route(task_type=ModelCapability.GENERAL)

            if emitter:
                emitter.emit(
                    stage="MODEL_SELECTING",
                    status="COMPLETED",
                    message=f"Model selected — {fallback_model.model_id}",
                    metadata={
                        "selected_model": fallback_model.model_id,
                        "requested_model": decision.requested_model_id,
                        "fallback_used": True,
                    },
                    run_id=run_id,
                )
                emitter.emit(
                    stage="GENERATING_OUTPUT",
                    status="STARTED",
                    message=f"Generating {output_label} with {fallback_model.model_id}",
                    run_id=run_id,
                )

            fb_start = time.perf_counter()
            response = fallback_model.generate(
                prompt,
                think=think,
                timeout=180.0,
                **kwargs,
            )
            fb_duration = time.perf_counter() - fb_start

            if emitter:
                emitter.emit(
                    stage="GENERATING_OUTPUT",
                    status="COMPLETED",
                    message=f"{output_label.capitalize()} generated",
                    metadata={"duration_seconds": round(fb_duration, 3)},
                    run_id=run_id,
                )

            return ModelExecutionResult(
                response=response,
                requested_model_id=decision.requested_model_id,
                actual_model_id=fallback_model.model_id,
                fallback_used=True,
                fallback_reason=reason,
                duration_seconds=round(fb_duration, 3),
                task_profile=profile,
            )