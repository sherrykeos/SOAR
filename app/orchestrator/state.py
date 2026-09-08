from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    task: str
    plan: list[Any] = field(default_factory=list)
    current_step: int = 0
    results: list[Any] = field(default_factory=list)
    observations: list[dict[str, Any]] = field(default_factory=list)
    iterations: int = 0
    max_iterations: int = 5
    status: str = "pending"