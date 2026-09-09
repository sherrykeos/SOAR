import time
from typing import Any, Dict

from app.tools.registry import ToolRegistry

from .action import ToolAction
from .events import EventStage, EventStatus, ProgressEventEmitter, sanitize_value
from .state import AgentState


class Executor:

    def __init__(
        self,
        tool_registry: ToolRegistry | None = None,
        emitter: ProgressEventEmitter | None = None,
    ):
        self.tool_registry = tool_registry or ToolRegistry()
        self.emitter = emitter

    def _get_friendly_start_message(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Constructs safe, user-friendly start message for UI cards."""
        if tool_name == "read_file":
            path = arguments.get("file_path", "file")
            return f"Reading {path}"
        elif tool_name == "pdf_reader":
            path = arguments.get("file_path", "PDF")
            return f"Extracting PDF text from {path}"
        elif tool_name == "docx_creator":
            path = arguments.get("output_path", arguments.get("file_path", "document"))
            return f"Creating DOCX document at {path}"
        elif tool_name == "pdf_creator":
            path = arguments.get("output_path", arguments.get("file_path", "PDF"))
            return f"Creating PDF document at {path}"
        elif tool_name == "search_knowledge":
            query = arguments.get("query", "")
            return f"Searching knowledge base for '{query}'" if query else "Searching knowledge base"
        elif tool_name == "python_sandbox":
            return "Executing Python code in sandbox"
        return f"Executing {tool_name}"

    def _get_safe_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Summarizes and truncates tool arguments for safe event metadata."""
        safe_args = {}
        for k, v in arguments.items():
            if k in ("content", "code", "text") and isinstance(v, str):
                safe_args[k] = (v[:100] + "... [truncated]") if len(v) > 100 else v
            else:
                safe_args[k] = sanitize_value(v, max_str_len=150)
        return safe_args

    def execute_action(
        self,
        action: ToolAction,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Executes a single ToolAction safely:
        1. Emits start event.
        2. Validates tool exists in registry.
        3. Validates arguments against declared tool schema.
        4. Executes tool and catches any runtime errors.
        5. Emits completion or failure event.
        """
        start_time = time.perf_counter()
        safe_args = self._get_safe_arguments(action.arguments)
        start_msg = self._get_friendly_start_message(action.tool, action.arguments)

        if self.emitter:
            self.emitter.emit(
                stage=EventStage.TOOL_EXECUTING,
                status=EventStatus.STARTED,
                message=start_msg,
                metadata={"tool": action.tool, "arguments": safe_args},
                run_id=run_id,
            )

        try:
            tool = self.tool_registry.get(action.tool)
        except KeyError:
            err = f"Tool '{action.tool}' not found in registry."
            duration = time.perf_counter() - start_time
            if self.emitter:
                self.emitter.emit(
                    stage=EventStage.TOOL_EXECUTING,
                    status=EventStatus.FAILED,
                    message=f"Tool execution failed — {action.tool}",
                    metadata={"tool": action.tool, "error": err, "duration_seconds": round(duration, 3)},
                    run_id=run_id,
                )
            return {
                "status": "error",
                "tool": action.tool,
                "error": err,
            }

        # Validate arguments against the tool's schema
        validation_error = tool.validate_arguments(action.arguments)
        if validation_error:
            err = f"Tool argument validation failed: {validation_error}"
            duration = time.perf_counter() - start_time
            if self.emitter:
                self.emitter.emit(
                    stage=EventStage.TOOL_EXECUTING,
                    status=EventStatus.FAILED,
                    message=f"Tool execution failed — {action.tool}",
                    metadata={"tool": action.tool, "error": err, "duration_seconds": round(duration, 3)},
                    run_id=run_id,
                )
            return {
                "status": "error",
                "tool": action.tool,
                "error": err,
            }

        try:
            result = tool.execute(**action.arguments)
            duration = time.perf_counter() - start_time

            # Check if tool output indicates an error
            if isinstance(result, str) and result.startswith("Error:"):
                if self.emitter:
                    self.emitter.emit(
                        stage=EventStage.TOOL_EXECUTING,
                        status=EventStatus.FAILED,
                        message=f"Tool execution failed — {action.tool}",
                        metadata={"tool": action.tool, "error": result, "duration_seconds": round(duration, 3)},
                        run_id=run_id,
                    )
                return {
                    "status": "error",
                    "tool": action.tool,
                    "error": result,
                    "result": result,
                }
            if isinstance(result, dict) and result.get("status") == "error":
                err_msg = result.get("error", "Tool reported an error status.")
                if self.emitter:
                    self.emitter.emit(
                        stage=EventStage.TOOL_EXECUTING,
                        status=EventStatus.FAILED,
                        message=f"Tool execution failed — {action.tool}",
                        metadata={"tool": action.tool, "error": err_msg, "duration_seconds": round(duration, 3)},
                        run_id=run_id,
                    )
                return {
                    "status": "error",
                    "tool": action.tool,
                    "error": err_msg,
                    "result": result,
                }

            if self.emitter:
                self.emitter.emit(
                    stage=EventStage.TOOL_EXECUTING,
                    status=EventStatus.COMPLETED,
                    message=f"Completed {action.tool}",
                    metadata={"tool": action.tool, "duration_seconds": round(duration, 3)},
                    run_id=run_id,
                )
            return {
                "status": "completed",
                "tool": action.tool,
                "result": result,
            }
        except Exception as e:
            duration = time.perf_counter() - start_time
            err_msg = f"Tool execution failed: {str(e)}"
            if self.emitter:
                self.emitter.emit(
                    stage=EventStage.TOOL_EXECUTING,
                    status=EventStatus.FAILED,
                    message=f"Tool execution failed — {action.tool}",
                    metadata={"tool": action.tool, "error": err_msg, "duration_seconds": round(duration, 3)},
                    run_id=run_id,
                )
            return {
                "status": "error",
                "tool": action.tool,
                "error": err_msg,
            }

    def execute(self, state: AgentState) -> AgentState:
        state.status = "running"

        for step in state.plan:
            if isinstance(step, ToolAction):
                print(f"Executing tool action: {step.tool} with arguments {step.arguments}")
                result = self.execute_action(step, run_id=state.run_id)
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