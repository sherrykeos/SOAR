import enum
import json
import re
import threading
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


class EventStage(str, enum.Enum):
    """
    Standard stages of SOAR execution checkpoints.
    """

    CLASSIFYING = "CLASSIFYING"
    MODEL_SELECTING = "MODEL_SELECTING"
    PLANNING = "PLANNING"
    TOOL_EXECUTING = "TOOL_EXECUTING"
    OBSERVING = "OBSERVING"
    REASONING = "REASONING"
    GENERATING_OUTPUT = "GENERATING_OUTPUT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EventStatus(str, enum.Enum):
    """
    Status of an execution checkpoint event.
    """

    STARTED = "STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


def sanitize_value(val: Any, max_str_len: int = 300) -> Any:
    """
    Sanitizes values to avoid leaking sensitive contents, secrets, or huge payloads.
    Strips raw chain-of-thought tags (<think>...</think>), passwords, and trims large strings.
    """
    if isinstance(val, str):
        # Remove chain-of-thought / think tags
        cleaned = re.sub(r"<think>[\s\S]*?</think>", "[thought stripped]", val, flags=re.IGNORECASE)
        # Redact common secret patterns
        cleaned = re.sub(r"(?i)(password|api_key|token|secret)\s*[:=]\s*['\"]?[^\s'\"]+['\"]?", r"\1: [REDACTED]", cleaned)
        if len(cleaned) > max_str_len:
            return cleaned[:max_str_len] + "... [truncated]"
        return cleaned
    elif isinstance(val, dict):
        return {str(k): sanitize_value(v, max_str_len) for k, v in val.items()}
    elif isinstance(val, (list, tuple)):
        return [sanitize_value(item, max_str_len) for item in val[:15]]
    return val


def sanitize_metadata(metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Sanitizes event metadata dictionaries for safe UI broadcast and logging.
    """
    if not metadata:
        return {}
    sanitized = {}
    sensitive_key_patterns = {"password", "api_key", "token", "secret", "credentials", "auth"}
    for k, v in metadata.items():
        k_str = str(k)
        k_lower = k_str.lower()
        # Exclude raw internal prompts or raw thought dumps
        if k_lower in ("raw_prompt", "full_prompt", "chain_of_thought", "raw_response"):
            continue
        # Redact known secret key names
        if any(sec in k_lower for sec in sensitive_key_patterns):
            sanitized[k_str] = "[REDACTED]"
            continue
        sanitized[k_str] = sanitize_value(v)
    return sanitized


@dataclass
class ProgressEvent:
    """
    Structured execution checkpoint event.
    Captures real backend state changes across the SOAR orchestrator loop.
    """

    stage: EventStage | str
    status: EventStatus | str
    message: str
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    run_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Ensure enum values are normalized to strings
        if isinstance(self.stage, enum.Enum):
            self.stage = self.stage.value
        if isinstance(self.status, enum.Enum):
            self.status = self.status.value
        # Ensure metadata is sanitized
        self.metadata = sanitize_metadata(self.metadata)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes event to dictionary suitable for JSON serialization."""
        return {
            "event_id": self.event_id,
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "stage": self.stage,
            "status": self.status,
            "message": self.message,
            "metadata": self.metadata,
        }


class BaseEventSink(ABC):
    """Abstract Base Class for progress event sinks."""

    @abstractmethod
    def handle_event(self, event: ProgressEvent) -> None:
        """Processes or forwards a progress event."""
        pass


class InMemoryEventSink(BaseEventSink):
    """
    Thread-safe in-memory sink that collects progress events in chronological order.
    Ideal for testing, synchronous API responses, and run history.
    """

    def __init__(self):
        self._events: List[ProgressEvent] = []
        self._lock = threading.Lock()

    def handle_event(self, event: ProgressEvent) -> None:
        with self._lock:
            self._events.append(event)

    def get_events(self) -> List[ProgressEvent]:
        with self._lock:
            return list(self._events)

    def get_event_dicts(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [e.to_dict() for e in self._events]

    def clear(self) -> None:
        with self._lock:
            self._events.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._events)


class CallbackEventSink(BaseEventSink):
    """
    Dispatches events to a registered subscriber callback.
    Enables future WebSocket, SSE, and real-time streaming interfaces.
    """

    def __init__(self, callback: Callable[[ProgressEvent], None]):
        self._callback = callback

    def handle_event(self, event: ProgressEvent) -> None:
        try:
            self._callback(event)
        except Exception:
            # Sinks should never crash the main agent flow
            pass


class ProgressEventEmitter:
    """
    Central emitter managing event sinks and dispatching real backend progress checkpoints.
    The Agent core depends solely on this emitter, remaining fully decoupled from UI/network logic.
    """

    def __init__(self, sinks: Optional[List[BaseEventSink]] = None):
        self._sinks: List[BaseEventSink] = list(sinks) if sinks else [InMemoryEventSink()]
        self._lock = threading.Lock()

    def add_sink(self, sink: BaseEventSink) -> None:
        """Registers a new event sink."""
        with self._lock:
            if sink not in self._sinks:
                self._sinks.append(sink)

    def remove_sink(self, sink: BaseEventSink) -> None:
        """Removes an existing event sink."""
        with self._lock:
            if sink in self._sinks:
                self._sinks.remove(sink)

    def subscribe(self, callback: Callable[[ProgressEvent], None]) -> CallbackEventSink:
        """Helper to attach a callback subscriber directly."""
        sink = CallbackEventSink(callback)
        self.add_sink(sink)
        return sink

    def emit_event(self, event: ProgressEvent) -> None:
        """Dispatches a constructed ProgressEvent to all registered sinks."""
        with self._lock:
            sinks_snapshot = list(self._sinks)

        for sink in sinks_snapshot:
            try:
                sink.handle_event(event)
            except Exception:
                # Sinks must not interrupt core orchestration
                pass

    def emit(
        self,
        stage: EventStage | str,
        status: EventStatus | str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        run_id: Optional[str] = None,
        event_id: Optional[str] = None,
    ) -> ProgressEvent:
        """
        Constructs and emits a new ProgressEvent.
        Returns the created event instance.
        """
        event = ProgressEvent(
            stage=stage,
            status=status,
            message=message,
            metadata=metadata or {},
            run_id=run_id,
            event_id=event_id or str(uuid.uuid4()),
        )
        self.emit_event(event)
        return event

    def get_in_memory_sink(self) -> Optional[InMemoryEventSink]:
        """Finds the first registered InMemoryEventSink, if any."""
        with self._lock:
            for sink in self._sinks:
                if isinstance(sink, InMemoryEventSink):
                    return sink
        return None

    def get_events(self) -> List[ProgressEvent]:
        """Retrieves all collected events from the in-memory sink."""
        sink = self.get_in_memory_sink()
        return sink.get_events() if sink else []

    def get_event_dicts(self) -> List[Dict[str, Any]]:
        """Retrieves all collected events as dictionaries from the in-memory sink."""
        sink = self.get_in_memory_sink()
        return sink.get_event_dicts() if sink else []

    def clear(self) -> None:
        """Clears events in the in-memory sink."""
        sink = self.get_in_memory_sink()
        if sink:
            sink.clear()
