from .action import ToolAction
from .executor import Executor
from .planner import Planner
from .state import AgentState


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
    ):
        self.planner = planner
        self.executor = executor
        self.max_iterations = max_iterations

    def run(self, task: str) -> AgentState:
        state = AgentState(
            task=task,
            max_iterations=self.max_iterations,
        )
        state.status = "running"

        while state.iterations < state.max_iterations:
            state.iterations += 1
            print(f"\n--- [AGENT ITERATION {state.iterations}/{state.max_iterations}] ---")

            # 1. PLAN / RE-PLAN
            state = self.planner.create_plan(state)

            if state.status == "error":
                print("[AGENT] Error encountered during planning. Halting loop.")
                break

            if state.status == "completed" or not state.plan:
                print("[AGENT] Task completed.")
                state.status = "completed"
                break

            # 2. ACT & 3. OBSERVE
            for step in state.plan:
                if isinstance(step, ToolAction):
                    print(f"Executing tool action: {step.tool} with arguments {step.arguments}")
                    action_result = self.executor.execute_action(step)
                    state.results.append(action_result)

                    # Capture Observation
                    observation = {
                        "iteration": state.iterations,
                        "tool": step.tool,
                        "arguments": step.arguments,
                        "status": action_result.get("status", "unknown"),
                        "result": action_result.get("result", action_result.get("error", "")),
                    }
                    state.observations.append(observation)
                    state.current_step += 1
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

        return state
