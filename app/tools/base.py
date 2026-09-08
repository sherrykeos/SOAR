from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseTool(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    def parameters(self) -> dict[str, dict[str, Any]]:
        """
        Returns a dictionary describing tool parameters and their schema:
        {
            "param_name": {
                "type": "string",
                "description": "...",
                "required": True
            }
        }
        """
        return {}

    def validate_arguments(self, arguments: dict[str, Any]) -> Optional[str]:
        """
        Validates provided arguments against the declared parameter schema.
        Returns an error message string if validation fails, or None if valid.
        """
        if not isinstance(arguments, dict):
            return f"Arguments must be a dictionary, got {type(arguments).__name__}."

        # Explicitly reject placeholder keys like 'parameter_name'
        if "parameter_name" in arguments:
            expected = list(self.parameters.keys())
            return (
                f"Invalid placeholder argument 'parameter_name'. "
                f"Please provide the actual parameter names from the tool schema: {expected}."
            )

        # Check required parameters
        for param_name, meta in self.parameters.items():
            if meta.get("required", False):
                val = arguments.get(param_name)
                # Support common standard aliases
                if val is None and param_name == "file_path":
                    val = arguments.get("path")
                elif val is None and param_name == "output_path":
                    val = arguments.get("file_path") or arguments.get("path")

                if val is None or (isinstance(val, str) and not val.strip()):
                    return (
                        f"Missing required parameter '{param_name}'. "
                        f"Expected: {meta.get('description', '')}"
                    )

        return None

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        pass