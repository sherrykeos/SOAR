from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolAction:
    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.tool, str) or not self.tool.strip():
            raise ValueError("ToolAction 'tool' must be a non-empty string.")
        if self.arguments is None:
            self.arguments = {}
        elif not isinstance(self.arguments, dict):
            raise TypeError("ToolAction 'arguments' must be a dictionary.")
