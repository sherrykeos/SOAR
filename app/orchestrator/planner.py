from app.models.manager import ModelManager
from app.tools.registry import ToolRegistry

from .events import EventStage, EventStatus, ProgressEventEmitter
from .plan_parser import PlanParseError, PlanParser
from .state import AgentState


class Planner:

    def __init__(
        self,
        model_manager: ModelManager,
        tool_registry: ToolRegistry | None = None,
        emitter: ProgressEventEmitter | None = None,
    ):
        self.model_manager = model_manager
        self.tool_registry = tool_registry
        self.emitter = emitter

    def _format_tools_description(self) -> str:
        if not self.tool_registry:
            return "No tools currently registered."

        tools = self.tool_registry.list_tools()
        if not tools:
            return "No tools currently registered."

        lines = ["Available tools:"]
        for tool in tools:
            lines.append("")
            if hasattr(tool, "get_schema_prompt"):
                lines.append(tool.get_schema_prompt())
            else:
                lines.append(f"Tool: {tool.name}")
                lines.append(f"Description: {tool.description}")
                if hasattr(tool, "parameters") and tool.parameters:
                    lines.append(f"Parameters: {list(tool.parameters.keys())}")
        return "\n".join(lines)

    def _format_task_context(self, state: AgentState) -> str:
        if not state.context:
            from .state import TaskContext
            state.context = TaskContext.from_task(state.task)

        ctx = state.context
        if not ctx.detected_paths:
            return ""

        lines = ["USER TASK CONTEXT & DETECTED PATHS:"]
        if ctx.input_paths:
            lines.append(f"- Input path(s) to read/analyze: {', '.join(ctx.input_paths)}")
        if ctx.output_paths:
            lines.append(f"- Output path(s) to create/save: {', '.join(ctx.output_paths)}")
        if ctx.detected_paths:
            lines.append(f"- All detected file paths: {', '.join(ctx.detected_paths)}")
        lines.append("CRITICAL: Use the exact paths listed above with full directory prefixes (do NOT strip 'inputs/' or 'outputs/').")
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
                f"Step {i}: Tool '{tool}' ({status}) | Arguments: {args}\nResult/Observation:\n{result}"
            )
        return "\n".join(lines)

    def create_plan(self, state: AgentState) -> AgentState:
        if self.emitter:
            self.emitter.emit(
                stage=EventStage.PLANNING,
                status=EventStatus.STARTED,
                message="Planning task",
                metadata={"iteration": state.iterations},
                run_id=state.run_id,
            )

        tools_desc = self._format_tools_description()
        context_desc = self._format_task_context(state)
        obs_desc = self._format_observations(state)

        context_block = f"\n{context_desc}\n" if context_desc else ""
        history_block = f"\n{obs_desc}\n" if obs_desc else ""

        prompt = f"""You are the planning component of SOAR, a sovereign on-premise AI agent.

TASK:
{state.task}
{context_block}
{tools_desc}
{history_block}
Rules:
- Output ONLY a valid JSON object matching the exact schema below.
- Do NOT wrap the JSON in markdown code fences.
- Do NOT include any explanations, preambles, or commentary.
- If the task is completed based on observations or no further actions are needed, return "status": "complete" and "steps": [].
- If more actions are needed, return "status": "continue" and provide the next step(s).
- Use ONLY tools listed under Available tools.
- In "arguments", use the EXACT parameter names defined in the tool's schema (e.g. "file_path", "output_path", "title", "content", "code", "query").
- NEVER use placeholder keys like "parameter_name".
- NEVER use placeholder values like "file_path" or "<actual_path>". Supply actual argument values.
- CRITICAL PATH RULES: Always copy file paths from the TASK exactly as written with their full directory prefixes (e.g. if TASK specifies "inputs/inspection_report.pdf", use "inputs/inspection_report.pdf", NOT "inspection_report.pdf"; if TASK specifies "outputs/approval_note.docx", use "outputs/approval_note.docx").
- ERROR RECOVERY: If a previous tool step failed or returned a validation error, analyze the error message and schema, and output a corrected action. Do NOT repeat the exact same failing arguments.
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
                if self.emitter:
                    self.emitter.emit(
                        stage=EventStage.PLANNING,
                        status=EventStatus.COMPLETED,
                        message="Plan completed",
                        metadata={"number_of_steps": 0, "tools": []},
                        run_id=state.run_id,
                    )
            else:
                state.plan = plan.steps
                state.status = "planned"
                if self.emitter:
                    step_tools = [s.tool for s in plan.steps if hasattr(s, "tool")]
                    self.emitter.emit(
                        stage=EventStage.PLANNING,
                        status=EventStatus.COMPLETED,
                        message="Plan created",
                        metadata={
                            "number_of_steps": len(plan.steps),
                            "tools": step_tools,
                        },
                        run_id=state.run_id,
                    )

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
            if self.emitter:
                self.emitter.emit(
                    stage=EventStage.PLANNING,
                    status=EventStatus.FAILED,
                    message="Plan creation failed",
                    metadata={"error": str(e)},
                    run_id=state.run_id,
                )

        return state