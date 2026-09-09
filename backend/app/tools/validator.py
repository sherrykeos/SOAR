from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ValidationResult:
    is_valid: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    argument: Optional[str] = None
    tool_name: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "tool_validation_error",
            "is_valid": self.is_valid,
            "code": self.error_code,
            "tool": self.tool_name,
            "argument": self.argument,
            "message": self.error_message,
            "details": self.details,
        }


class ToolValidator:
    """
    Validates tool execution arguments against declared tool parameter schemas.
    Catches missing arguments, unknown/misspelled arguments, placeholder keys,
    and type mismatches before tool execution.
    """

    # Common acceptable aliases for standard parameter names
    PARAM_ALIASES: Dict[str, List[str]] = {
        "file_path": ["path", "filepath"],
        "output_path": ["output_file", "save_path", "target_path"],
        "query": ["search_query", "q"],
        "code": ["script", "python_code"],
    }

    @classmethod
    def validate(cls, tool: Any, arguments: Any) -> ValidationResult:
        tool_name = getattr(tool, "name", "unknown_tool")
        parameters = getattr(tool, "parameters", {}) or {}

        # If a custom or mock tool has not declared parameters, allow execution
        if not parameters:
            return ValidationResult(is_valid=True, tool_name=tool_name)

        if not isinstance(arguments, dict):
            return ValidationResult(
                is_valid=False,
                error_code="invalid_argument_type",
                error_message=f"Tool arguments must be a JSON dictionary/object, got {type(arguments).__name__}.",
                tool_name=tool_name,
                details={"expected": "dictionary", "received": type(arguments).__name__},
            )

        # 1. Check for placeholder keys (e.g., {"parameter_name": "file_path"})
        if "parameter_name" in arguments:
            allowed = list(parameters.keys())
            return ValidationResult(
                is_valid=False,
                error_code="placeholder_key_detected",
                error_message=(
                    f"Invalid placeholder argument 'parameter_name'. "
                    f"Please provide the actual parameter names from the tool schema: {allowed}."
                ),
                argument="parameter_name",
                tool_name=tool_name,
                details={"allowed_parameters": allowed},
            )

        # 2. Check for unknown arguments
        allowed_keys = set(parameters.keys())
        for canonical, aliases in cls.PARAM_ALIASES.items():
            if canonical in allowed_keys:
                allowed_keys.update(aliases)

        for arg_name in arguments.keys():
            if arg_name not in allowed_keys:
                valid_params = list(parameters.keys())
                return ValidationResult(
                    is_valid=False,
                    error_code="unknown_argument",
                    error_message=(
                        f"Unknown argument '{arg_name}' for tool '{tool_name}'. "
                        f"Allowed parameters: {valid_params}."
                    ),
                    argument=arg_name,
                    tool_name=tool_name,
                    details={"unknown_argument": arg_name, "allowed_parameters": valid_params},
                )

        # 3. Check for required arguments and type validation
        for param_name, meta in parameters.items():
            is_required = meta.get("required", False)
            expected_type = meta.get("type", "string")

            # Check canonical name or known aliases
            val = arguments.get(param_name)
            if val is None:
                for alias in cls.PARAM_ALIASES.get(param_name, []):
                    if alias in arguments:
                        val = arguments[alias]
                        break

            if is_required:
                if val is None or (isinstance(val, str) and not val.strip()):
                    return ValidationResult(
                        is_valid=False,
                        error_code="missing_argument",
                        error_message=(
                            f"Missing required parameter '{param_name}'. "
                            f"Expected: {meta.get('description', '')}"
                        ),
                        argument=param_name,
                        tool_name=tool_name,
                        details={"parameter": param_name, "description": meta.get("description", "")},
                    )

            # Type validation if value is provided
            if val is not None:
                type_err = cls._validate_type(param_name, val, expected_type)
                if type_err:
                    return ValidationResult(
                        is_valid=False,
                        error_code="type_mismatch",
                        error_message=f"Argument '{param_name}' for tool '{tool_name}' {type_err}",
                        argument=param_name,
                        tool_name=tool_name,
                        details={"parameter": param_name, "expected_type": expected_type},
                    )

        return ValidationResult(is_valid=True, tool_name=tool_name)

    @classmethod
    def _validate_type(cls, param_name: str, val: Any, expected_type: str) -> Optional[str]:
        if expected_type == "string":
            if not isinstance(val, str):
                return f"must be a string, got {type(val).__name__}."
        elif expected_type == "integer":
            if isinstance(val, bool) or not isinstance(val, int):
                try:
                    int(str(val))
                except (ValueError, TypeError):
                    return f"must be an integer, got {type(val).__name__}."
        elif expected_type == "boolean":
            if not isinstance(val, bool):
                return f"must be a boolean (True/False), got {type(val).__name__}."
        elif expected_type in ("list", "array"):
            if not isinstance(val, list):
                return f"must be a list, got {type(val).__name__}."
        elif expected_type in ("dict", "object"):
            if not isinstance(val, dict):
                return f"must be a dictionary, got {type(val).__name__}."
        return None

    @classmethod
    def format_error_observation(
        cls,
        tool: Any,
        validation: ValidationResult,
        task_context: Optional[Any] = None,
    ) -> str:
        """
        Formats a detailed, actionable error message for the planner with correction guidance.
        """
        tool_name = getattr(tool, "name", "unknown_tool")
        parameters = getattr(tool, "parameters", {}) or {}

        req_params = [f"- {k} ({v.get('type', 'string')}): {v.get('description', '')}" for k, v in parameters.items() if v.get("required", False)]
        opt_params = [f"- {k} ({v.get('type', 'string')}): {v.get('description', '')}" for k, v in parameters.items() if not v.get("required", False)]

        lines = [
            f"Tool action validation failed.",
            f"",
            f"Tool: {tool_name}",
            f"Problem: {validation.error_message}",
            f"",
            f"Required arguments:",
            *(req_params if req_params else ["  None"]),
        ]

        if opt_params:
            lines.append("Optional arguments:")
            lines.extend(opt_params)

        # Build realistic example
        sample_args = {}
        for k, v in parameters.items():
            if v.get("required", False):
                if k in ("file_path", "path"):
                    sample_args[k] = "<actual_input_path>"
                elif k in ("output_path", "save_path"):
                    sample_args[k] = "<actual_output_path>"
                elif k == "content":
                    sample_args[k] = "<text_content>"
                elif k == "code":
                    sample_args[k] = "<python_code>"
                elif k == "query":
                    sample_args[k] = "<search_query>"
                else:
                    sample_args[k] = f"<{k}>"

        import json
        example_json = json.dumps({"tool": tool_name, "arguments": sample_args}, indent=2)
        lines.append("")
        lines.append(f"Correct action format:")
        lines.append(example_json)

        if task_context:
            detected = getattr(task_context, "detected_paths", [])
            if detected:
                lines.append("")
                lines.append(f"Paths mentioned in original task: {detected}")

        return "\n".join(lines)
