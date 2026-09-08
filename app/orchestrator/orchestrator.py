# Vajra pipeline

from app.models.manager import ModelManager

from .state import AgentState
from .planner import Planner
from .executor import Executor


class Orchestrator:

    def __init__(self):
        self.model_manager = ModelManager()

        self.planner = Planner(
            self.model_manager
        )

        self.executor = Executor()

    def run(self, task: str) -> AgentState:
        state = AgentState(task=task)

        state = self.planner.create_plan(state)

        state = self.executor.execute(state)

        return state