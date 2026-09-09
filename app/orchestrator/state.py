import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    task: str
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    plan: list[Any] = field(default_factory=list)
    current_step: int = 0
    results: list[Any] = field(default_factory=list)
    observations: list[dict[str, Any]] = field(default_factory=list)
    events: list[Any] = field(default_factory=list)
    iterations: int = 0
    max_iterations: int = 5
    status: str = "pending"