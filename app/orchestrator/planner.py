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
            lines.append(f"\nTool: {tool.name}")
            lines.append(f"Description: {tool.description}")
            if hasattr(tool, "parameters") and tool.parameters:
                req_params = [
                    (k, v) for k, v in tool.parameters.items() if v.get("required", False)
                ]
                opt_params = [
                    (k, v) for k, v in tool.parameters.items() if not v.get("required", False)
                ]
                if req_params:
                    lines.append("Required parameters:")
                    for p_name, p_meta in req_params:
                        lines.append(f"  - {p_name}: {p_meta.get('description', '')}")
                if opt_params:
                    lines.append("Optional parameters:")
                    for p_name, p_meta in opt_params:
                        lines.append(f"  - {p_name}: {p_meta.get('description', '')}")
            else:
                lines.append("Parameters: none")
        return "\n".join(lines)

    def _format_observations(self, state: AgentState) -> str:
        if not state.observations:
            return ""

        lines = ["PREVIOUS OBSERVATIONS & RESULTS:"]
        for i, obs in enumerate(state.observations, 1):
            tool = obs.get("tool", "unknown")
            args = obs.get("arguments", {})
            status = obs.get("status", "unknown")
            result = obs.get("result", "")
            lines.append(
                f"Step {i}: Tool '{tool}' ({status}) | Arguments: {args} | Result: {result}"
            )
        return "\n".join(lines)

    def create_plan(self, state: AgentState) -> AgentState:
        tools_desc = self._format_tools_description()
        obs_desc = self._format_observations(state)

        history_block = f"\n{obs_desc}\n" if obs_desc else ""

        prompt = f"""You are the planning component of SOAR, a sovereign on-premise AI agent.

TASK:
{state.task}

{tools_desc}
{history_block}
Rules:
- Output ONLY a valid JSON object matching the exact schema below.
- Do NOT wrap the JSON in markdown code fences.
- Do NOT include any explanations, preambles, or commentary.
- If the task is completed based on observations or no further actions are needed, return "status": "complete" and "steps": [].
- If more actions are needed, return "status": "continue" and provide the next step(s).
- Use only tools listed under Available tools.
- In "arguments", use the EXACT parameter names defined in the tool's parameter list (e.g. "file_path", "output_path", "title", "content", "code"). Do NOT use "parameter_name" as a key.
- CRITICAL PATH RULES: Always copy file paths from the TASK exactly as written with their full directory prefixes (e.g. if TASK specifies "inputs/inspection_report.pdf", use "inputs/inspection_report.pdf", NOT "inspection_report.pdf"; if TASK specifies "outputs/approval_note.docx", use "outputs/approval_note.docx").
- ERROR RECOVERY: If a previous tool step failed or returned an error, analyze the error message and do NOT repeat the exact same failing arguments. Fix the argument values or take a different action.
- Keep the plan between 0 and 5 steps.
- Do not execute the task yourself.

Exact JSON Schema:
{{
  "status": "continue" | "complete",
  "thought": "brief reasoning",
  "steps": [
    {{
      "tool": "<tool_name>",
      "arguments": {{
        "<actual_param_name>": "<value>"
      }}
    }}
  ]
}}"""

        print("\n===== SENDING TO MODEL =====")
        print(prompt)
        print("============================\n")

        response = self.model_manager.generate(prompt, task_type="reasoning")

        print("\n===== PLANNER RESPONSE =====\n")
        print(response)
        print("============================\n")

        try:
            plan = PlanParser.parse(response)
            if self.tool_registry is not None:
                PlanParser.validate_tools(plan, self.tool_registry)

            if plan.status == "complete" or not plan.steps:
                state.plan = []
                state.status = "completed"
            else:
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