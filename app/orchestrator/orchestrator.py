# Vajra pipeline

from app.models.manager import ModelManager
from app.tools.read_file import ReadFileTool
from app.tools.registry import ToolRegistry

from .executor import Executor
from .planner import Planner
from .state import AgentState


class Orchestrator:

    def __init__(self, tool_registry: ToolRegistry | None = None):
        self.model_manager = ModelManager()

        if tool_registry is None:
            self.tool_registry = ToolRegistry()
            self._register_default_tools()
        else:
            self.tool_registry = tool_registry

        self.planner = Planner(
            self.model_manager,
            tool_registry=self.tool_registry,
        )

        self.executor = Executor(
            tool_registry=self.tool_registry,
        )

    def _register_default_tools(self) -> None:
        self.tool_registry.register(ReadFileTool())

    def run(self, task: str) -> AgentState:
        state = AgentState(task=task)

        state = self.planner.create_plan(state)

        if state.status == "error":
            print("[ORCHESTRATOR] Planning failed. Halting execution.")
            return state

        state = self.executor.execute(state)

        return state