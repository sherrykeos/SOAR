from dataclasses import dataclass, field

from .action import ToolAction


@dataclass
class StructuredPlan:
    steps: list[ToolAction] = field(default_factory=list)
    status: str = "continue"
    thought: str = ""
