import json
from typing import Any

from .action import ToolAction
from .events import EventStage, EventStatus, ProgressEventEmitter, sanitize_value
from .executor import Executor
from .planner import Planner
from .state import AgentState, TaskContext


class Agent:
    """
    Coordinates the SOAR Agent Loop:
    Plan -> Act -> Observe -> Re-plan -> ... -> Complete
    """

    def __init__(
        self,
        planner: Planner,
        executor: Executor,
        max_iterations: int = 5,
        emitter: ProgressEventEmitter | None = None,
    ):
        self.planner = planner
        self.executor = executor
        self.max_iterations = max_iterations
        self.emitter = emitter

        # Propagate emitter to planner and executor if not already set
        if self.emitter:
            if not getattr(self.planner, "emitter", None):
                self.planner.emitter = self.emitter
            if not getattr(self.executor, "emitter", None):
                self.executor.emitter = self.emitter

    def _get_safe_result_summary(self, result: Any) -> str:
        """Constructs a short, safe summary of the tool result for observation metadata."""
        if isinstance(result, str):
            clean = result.replace("\n", " ").strip()
            return clean[:120] + "... [truncated]" if len(clean) > 120 else clean
        elif isinstance(result, dict):
            status = result.get("status", "unknown")
            count = result.get("count")
            if count is not None:
                return f"status: {status}, count: {count}"
            return f"status: {status}"
        return str(result)[:100]

    def run(self, task: str) -> AgentState:
        state = AgentState(
            task=task,
            max_iterations=self.max_iterations,
            context=TaskContext.from_task(task),
        )
        state.status = "running"

        while state.iterations < state.max_iterations:
            state.iterations += 1
            print(f"\n--- [AGENT ITERATION {state.iterations}/{state.max_iterations}] ---")

            # Emit REASONING event when analyzing results in subsequent iterations
            if state.iterations > 1 and self.emitter:
                self.emitter.emit(
                    stage=EventStage.REASONING,
                    status=EventStatus.IN_PROGRESS,
                    message="Analyzing results",
                    metadata={"iteration": state.iterations},
                    run_id=state.run_id,
                )

            # 1. PLAN / RE-PLAN
            state = self.planner.create_plan(state)

            if state.status == "error":
                print("[AGENT] Error encountered during planning. Halting loop.")
                if self.emitter:
                    self.emitter.emit(
                        stage=EventStage.FAILED,
                        status=EventStatus.FAILED,
                        message="Task failed during planning",
                        metadata={"status": "error", "iterations": state.iterations},
                        run_id=state.run_id,
                    )
                break

            if state.status == "completed" or not state.plan:
                print("[AGENT] Task completed.")
                state.status = "completed"
                if self.emitter:
                    self.emitter.emit(
                        stage=EventStage.COMPLETED,
                        status=EventStatus.COMPLETED,
                        message="Task completed",
                        metadata={"iterations": state.iterations, "status": "completed"},
                        run_id=state.run_id,
                    )
                break

            # 2. ACT & 3. OBSERVE
            for step in state.plan:
                if isinstance(step, ToolAction):
                    # Check failure fingerprint to prevent repeating identical failing actions
                    try:
                        norm_args = json.dumps(step.arguments, sort_keys=True)
                    except (TypeError, ValueError):
                        norm_args = str(step.arguments)

                    prev_failure = next(
                        (f for f in state.failure_fingerprints if f.get("tool") == step.tool and f.get("args") == norm_args),
                        None
                    )

                    if prev_failure:
                        print(f"[AGENT] Intercepted repeated failing action: {step.tool} with {step.arguments}")
                        prev_err_msg = prev_failure.get("error", "Action previously failed.")
                        repeated_obs_msg = (
                            f"REPEATED FAILING ACTION DETECTED:\n"
                            f"The action '{step.tool}' with arguments {step.arguments} already failed previously in this run with error:\n"
                            f"'{prev_err_msg}'\n\n"
                            f"DO NOT repeat the exact same failing action. Correct the argument names, fix file paths, or choose another valid approach."
                        )
                        action_result = {
                            "status": "error",
                            "tool": step.tool,
                            "error": repeated_obs_msg,
                            "is_repeated_failure": True,
                        }
                        state.results.append(action_result)
                        state.observations.append({
                            "iteration": state.iterations,
                            "tool": step.tool,
                            "arguments": step.arguments,
                            "status": "error",
                            "result": repeated_obs_msg,
                        })
                        state.current_step += 1
                        if self.emitter:
                            self.emitter.emit(
                                stage=EventStage.TOOL_EXECUTING,
                                status=EventStatus.FAILED,
                                message=f"Repeated action prevented — {step.tool}",
                                metadata={"tool": step.tool, "reason": "repeated_failure"},
                                run_id=state.run_id,
                            )
                        continue

                    print(f"Executing tool action: {step.tool} with arguments {step.arguments}")
                    action_result = self.executor.execute_action(
                        step,
                        run_id=state.run_id,
                        context=state.context,
                    )
                    state.results.append(action_result)

                    # Record failure fingerprint if action failed
                    raw_res = action_result.get("result", action_result.get("error", ""))
                    if action_result.get("status") == "error":
                        state.failure_fingerprints.append({
                            "tool": step.tool,
                            "args": norm_args,
                            "error": str(raw_res)[:300],
                        })

                    # Capture Observation
                    observation = {
                        "iteration": state.iterations,
                        "tool": step.tool,
                        "arguments": step.arguments,
                        "status": action_result.get("status", "unknown"),
                        "result": raw_res,
                    }
                    state.observations.append(observation)
                    state.current_step += 1

                    # Emit OBSERVING event
                    if self.emitter:
                        summary = self._get_safe_result_summary(raw_res)
                        self.emitter.emit(
                            stage=EventStage.OBSERVING,
                            status=EventStatus.COMPLETED,
                            message="Observation received",
                            metadata={
                                "tool": step.tool,
                                "success": action_result.get("status") == "completed",
                                "result_summary": summary,
                            },
                            run_id=state.run_id,
                        )
                else:
                    print(f"Executing step: {step}")
                    state.results.append(
                        {
                            "step": step,
                            "status": "completed",
                        }
                    )
                    state.current_step += 1

            # Clear plan for next re-planning iteration
            state.plan = []

        if state.iterations >= state.max_iterations and state.status not in ("completed", "error"):
            print("[AGENT] Maximum iterations reached without task completion.")
            state.status = "max_iterations_reached"
            if self.emitter:
                self.emitter.emit(
                    stage=EventStage.FAILED,
                    status=EventStatus.FAILED,
                    message="Task failed — maximum iterations reached",
                    metadata={"status": "max_iterations_reached", "iterations": state.iterations},
                    run_id=state.run_id,
                )

        if self.emitter:
            state.events = self.emitter.get_events()

        return state
