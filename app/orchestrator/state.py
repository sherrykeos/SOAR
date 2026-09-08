# This represents the state of a running agent task.
# The important idea is that the agent has state.
# Later, this will allow Vajra to remember:

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    task: str
    plan: list[str] = field(default_factory=list)
    current_step: int = 0
    results: list[Any] = field(default_factory=list)
    status: str = "pending"