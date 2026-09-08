from .state import AgentState


class Executor:

    def execute(self, state: AgentState) -> AgentState:
        state.status = "running"

        for step in state.plan:
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