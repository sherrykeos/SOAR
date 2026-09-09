import json
import re
from typing import Any, Union

from app.tools.registry import ToolRegistry

from ..execution.action import ToolAction
from ..execution.action_parser import ActionParseError, ActionParser
from .plan import StructuredPlan


class PlanParseError(ValueError):
    """Raised when parsing or validating a structured plan fails."""
    pass


class PlanParser:

    @staticmethod
    def _strip_markdown_code_fences(text: str) -> str:
        """Strips markdown code fences (e.g. ```json ... ```) and isolates JSON."""
        trimmed = text.strip()

        # Check for code fence block
        pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        match = re.search(pattern, trimmed, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # If wrapped in curly braces within other commentary, extract outer { ... }
        first_brace = trimmed.find("{")
        last_brace = trimmed.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            return trimmed[first_brace : last_brace + 1].strip()

        return trimmed

    @classmethod
    def parse(cls, data: Union[str, dict[str, Any]]) -> StructuredPlan:
        """
        Parses a JSON string or dictionary into a StructuredPlan.

        Expected schema:
        {
            "status": "continue" | "complete",
            "thought": "optional reasoning",
            "steps": [
                {
                    "tool": "tool_name",
                    "arguments": { ... }
                }
            ]
        }
        """
        if isinstance(data, str):
            cleaned = cls._strip_markdown_code_fences(data)
            try:
                parsed = json.loads(cleaned)
            except json.JSONDecodeError as e:
                raise PlanParseError(f"Invalid JSON format in plan: {e.msg}") from e
        elif isinstance(data, dict):
            parsed = data
        else:
            raise PlanParseError(
                f"Plan data must be a JSON string or dict, got {type(data).__name__}"
            )

        if not isinstance(parsed, dict):
            raise PlanParseError(
                f"Plan root must be a JSON object/dict, got {type(parsed).__name__}"
            )

        raw_status = str(parsed.get("status", "continue")).strip().lower()
        if raw_status in ("complete", "completed", "finish", "done"):
            plan_status = "complete"
        else:
            plan_status = "continue"

        thought = str(parsed.get("thought", parsed.get("reasoning", "")))

        # Handle 'steps' field
        if "steps" not in parsed:
            if plan_status == "complete":
                raw_steps = []
            else:
                raise PlanParseError("Plan missing required 'steps' field.")
        else:
            raw_steps = parsed["steps"]

        if not isinstance(raw_steps, list):
            raise PlanParseError(
                f"Plan 'steps' field must be a list, got {type(raw_steps).__name__}."
            )

        steps: list[ToolAction] = []
        for i, step in enumerate(raw_steps):
            try:
                action = ActionParser.parse(step)
                steps.append(action)
            except (ActionParseError, ValueError, TypeError) as e:
                raise PlanParseError(f"Malformed action at step {i}: {str(e)}") from e

        # If no steps provided and status not explicitly continue, consider complete
        if not steps and "status" not in parsed:
            plan_status = "complete"

        return StructuredPlan(steps=steps, status=plan_status, thought=thought)

    @classmethod
    def validate_tools(cls, plan: StructuredPlan, tool_registry: ToolRegistry) -> None:
        """
        Validates that all tools referenced in the plan exist in the ToolRegistry.
        Raises PlanParseError if an unknown tool is encountered.
        """
        if not plan.steps:
            return

        registered_tools = {t.name for t in tool_registry.list_tools()}
        for i, action in enumerate(plan.steps):
            if action.tool not in registered_tools:
                raise PlanParseError(
                    f"Unknown tool '{action.tool}' at step {i}. Registered tools: {sorted(list(registered_tools))}"
                )
