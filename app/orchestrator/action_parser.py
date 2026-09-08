import json
from typing import Any, Union

from .action import ToolAction


class ActionParseError(ValueError):
    """Raised when parsing a structured action fails."""
    pass


class ActionParser:

    @staticmethod
    def parse(data: Union[str, dict[str, Any]]) -> ToolAction:
        """
        Parses a JSON string or dictionary into a ToolAction object.

        Expected format:
        {
            "tool": "tool_name",
            "arguments": { ... }  # optional, defaults to {}
        }
        """
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
            except json.JSONDecodeError as e:
                raise ActionParseError(f"Invalid JSON format: {e.msg}") from e
        elif isinstance(data, dict):
            parsed = data
        else:
            raise ActionParseError(
                f"Action data must be a JSON string or dict, got {type(data).__name__}"
            )

        if not isinstance(parsed, dict):
            raise ActionParseError(
                f"Action root must be a JSON object/dict, got {type(parsed).__name__}"
            )

        tool = parsed.get("tool")
        if not tool or not isinstance(tool, str) or not tool.strip():
            raise ActionParseError("Action missing required non-empty 'tool' field.")

        arguments = parsed.get("arguments", {})
        if arguments is None:
            arguments = {}
        elif not isinstance(arguments, dict):
            raise ActionParseError(
                f"Action 'arguments' must be a dictionary, got {type(arguments).__name__}."
            )

        return ToolAction(tool=tool.strip(), arguments=arguments)
