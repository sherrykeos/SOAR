from app.models.manager import ModelManager
from app.tools.registry import ToolRegistry

from .plan_parser import PlanParseError, PlanParser
from .state import AgentState


class Planner:

    def __init__(
        self,
        model_manager: ModelManager,
        tool_registry: ToolRegistry | None = None,
    ):
        self.model_manager = model_manager
        self.tool_registry = tool_registry

    def _format_tools_description(self) -> str:
        if not self.tool_registry:
            return "No tools currently registered."

        tools = self.tool_registry.list_tools()
        if not tools:
            return "No tools currently registered."

        lines = ["Available tools:"]
        for tool in tools:
            lines.append(f"- {tool.name}: {tool.description}")
        return "\n".join(lines)

    def create_plan(self, state: AgentState) -> AgentState:
        tools_desc = self._format_tools_description()

        prompt = f"""You are the planning component of SOAR, a sovereign on-premise AI agent.

Create an executable structured plan for the following task using ONLY the registered tools.

TASK:
{state.task}

{tools_desc}

Rules:
- Output ONLY a valid JSON object matching the exact schema below.
- Do NOT wrap the JSON in markdown code fences.
- Do NOT include any explanations, preambles, or commentary.
- Use only tools listed under Available tools.
- Keep the plan between 1 and 6 steps.
- Do not execute the task.

Exact JSON Schema:
{{
  "steps": [
    {{
      "tool": "tool_name",
      "arguments": {{
        "parameter_name": "value"
      }}
    }}
  ]
}}"""

        print("\n===== SENDING TO MODEL =====")
        print(prompt)
        print("============================\n")

        response = self.model_manager.generate(prompt, task_type="reasoning")

        print("\n===== PLANNER RESPONSE =====")
        print(response)
        print("============================\n")

        try:
            plan = PlanParser.parse(response)
            if self.tool_registry is not None:
                PlanParser.validate_tools(plan, self.tool_registry)

            state.plan = plan.steps
            state.status = "planned"
        except PlanParseError as e:
            print(f"[PLANNER ERROR] {e}")
            state.status = "error"
            state.results.append(
                {
                    "status": "error",
                    "error": f"Plan parsing/validation failed: {str(e)}",
                    "raw_response": response,
                }
            )

        return state