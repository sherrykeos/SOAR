# For now, a fake planner:
from .state import AgentState


class Planner:

    def create_plan(self, state: AgentState) -> AgentState:
        state.plan = [
            "Understand the task",
            "Execute the required operation",
            "Verify the result",
        ]

        return state