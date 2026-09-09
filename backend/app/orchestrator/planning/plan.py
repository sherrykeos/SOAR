from dataclasses import dataclass, field

from ..execution.action import ToolAction


@dataclass
class StructuredPlan:
    steps: list[ToolAction] = field(default_factory=list)
    status: str = "continue"
    thought: str = ""
