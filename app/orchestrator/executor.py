from typing import Any

from app.tools.registry import ToolRegistry

from .action import ToolAction
from .state import AgentState


class Executor:

    def __init__(self, tool_registry: ToolRegistry | None = None):
        self.tool_registry = tool_registry or ToolRegistry()

    def execute_action(self, action: ToolAction) -> dict[str, Any]:
        """
        Executes a single ToolAction safely:
        1. Validates tool exists in registry.
        2. Validates arguments against declared tool schema.
        3. Executes tool and catches any runtime errors.
        4. Identifies error return strings and flags status as 'error'.
        """
        try:
            tool = self.tool_registry.get(action.tool)
        except KeyError:
            return {
                "status": "error",
                "tool": action.tool,
                "error": f"Tool '{action.tool}' not found in registry.",
            }

        # Validate arguments against the tool's schema
        validation_error = tool.validate_arguments(action.arguments)
        if validation_error:
            return {
                "status": "error",
                "tool": action.tool,
                "error": f"Tool argument validation failed: {validation_error}",
            }

        try:
            result = tool.execute(**action.arguments)
            # Check if tool output indicates an error
            if isinstance(result, str) and result.startswith("Error:"):
                return {
                    "status": "error",
                    "tool": action.tool,
                    "error": result,
                    "result": result,
                }
            return {
                "status": "completed",
                "tool": action.tool,
                "result": result,
            }
        except Exception as e:
            return {
                "status": "error",
                "tool": action.tool,
                "error": f"Tool execution failed: {str(e)}",
            }

    def execute(self, state: AgentState) -> AgentState:
        state.status = "running"

        for step in state.plan:
            if isinstance(step, ToolAction):
                print(f"Executing tool action: {step.tool} with arguments {step.arguments}")
                result = self.execute_action(step)
                state.results.append(result)
            else:
                print(f"Executing: {step}")
                state.results.append(
                    {
                        "step": step,
                        "status": "completed",
                    }
                )

            state.current_step += 1

        state.status = "completed"

        return state