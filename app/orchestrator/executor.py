from typing import Any

from app.tools.registry import ToolRegistry

from .action import ToolAction
from .state import AgentState


class Executor:

    def __init__(self, tool_registry: ToolRegistry | None = None):
        self.tool_registry = tool_registry or ToolRegistry()

    def execute_action(self, action: ToolAction) -> dict[str, Any]:
        """Executes a single ToolAction through the ToolRegistry safely."""
        try:
            tool = self.tool_registry.get(action.tool)
        except KeyError:
            return {
                "status": "error",
                "tool": action.tool,
                "error": f"Tool '{action.tool}' not found in registry.",
            }

        try:
            result = tool.execute(**action.arguments)
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