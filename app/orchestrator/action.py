from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolAction:
    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)
