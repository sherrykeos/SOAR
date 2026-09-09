from abc import ABC, abstractmethod
import json
from typing import Any, Optional

from .validator import ToolValidator, ValidationResult


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

    def get_schema_prompt(self) -> str:
        """
        Generates an explicit tool schema description with concrete JSON usage example for the planner.
        """
        lines = [
            f"Tool: {self.name}",
            f"Description: {self.description}",
        ]
        params = self.parameters
        if params:
            req_params = [(k, v) for k, v in params.items() if v.get("required", False)]
            opt_params = [(k, v) for k, v in params.items() if not v.get("required", False)]

            if req_params:
                lines.append("Required parameters:")
                for p_name, p_meta in req_params:
                    p_type = p_meta.get("type", "string")
                    lines.append(f"  - {p_name}: {p_meta.get('description', '')} (type: {p_type})")
            else:
                lines.append("Required parameters: none")

            if opt_params:
                lines.append("Optional parameters:")
                for p_name, p_meta in opt_params:
                    p_type = p_meta.get("type", "string")
                    lines.append(f"  - {p_name}: {p_meta.get('description', '')} (type: {p_type})")

            # Generate concrete example action
            sample_args = {}
            for k, v in params.items():
                if v.get("required", False):
                    if k in ("file_path", "path"):
                        sample_args[k] = "inputs/sample.pdf" if "pdf" in self.name else "inputs/sample.txt"
                    elif k in ("output_path", "save_path"):
                        sample_args[k] = "outputs/result.docx" if "docx" in self.name else "outputs/result.pdf"
                    elif k == "content":
                        sample_args[k] = "Document text content..."
                    elif k == "code":
                        sample_args[k] = "print('Hello SOAR')"
                    elif k == "query":
                        sample_args[k] = "system status"
                    else:
                        sample_args[k] = f"<{k}_value>"

            example_dict = {"tool": self.name, "arguments": sample_args}
            lines.append("Example action:")
            lines.append(json.dumps(example_dict, indent=2))
        else:
            lines.append("Arguments: none")
            lines.append("Example action:")
            lines.append(json.dumps({"tool": self.name, "arguments": {}}, indent=2))

        return "\n".join(lines)

    def validate_action(self, arguments: dict[str, Any]) -> ValidationResult:
        """
        Validates arguments and returns a structured ValidationResult object.
        """
        return ToolValidator.validate(self, arguments)

    def validate_arguments(self, arguments: dict[str, Any]) -> Optional[str]:
        """
        Validates provided arguments against the declared parameter schema.
        Returns an error message string if validation fails, or None if valid.
        Maintains backwards compatibility with existing callers.
        """
        result = self.validate_action(arguments)
        if not result.is_valid:
            return result.error_message
        return None

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        pass