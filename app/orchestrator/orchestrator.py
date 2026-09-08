# Vajra pipeline

from .state import AgentState
from .planner import Planner
from .executor import Executor


class Orchestrator:

    def __init__(self):
        self.planner = Planner()
        self.executor = Executor()

    def run(self, task: str) -> AgentState:
        state = AgentState(task=task)

        state = self.planner.create_plan(state)
        state = self.executor.execute(state)

        return state