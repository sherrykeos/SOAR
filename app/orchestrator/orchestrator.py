# Vajra pipeline

from app.models.manager import ModelManager
from app.tools.docx_creator import DOCXCreatorTool
from app.tools.pdf_creator import PDFCreatorTool
from app.tools.pdf_reader import PDFReaderTool
from app.tools.python_sandbox import PythonSandboxTool
from app.tools.read_file import ReadFileTool
from app.tools.registry import ToolRegistry
from app.tools.search_knowledge import SearchKnowledgeTool

from .agent import Agent
from .executor import Executor
from .planner import Planner
from .state import AgentState


class Orchestrator:

    def __init__(
        self,
        tool_registry: ToolRegistry | None = None,
        model_manager: ModelManager | None = None,
        max_iterations: int = 5,
    ):
        self.model_manager = model_manager or ModelManager()

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

        self.agent = Agent(
            planner=self.planner,
            executor=self.executor,
            max_iterations=max_iterations,
        )

    def _register_default_tools(self) -> None:
        self.tool_registry.register(ReadFileTool())
        self.tool_registry.register(PDFReaderTool())
        self.tool_registry.register(DOCXCreatorTool())
        self.tool_registry.register(PDFCreatorTool())
        self.tool_registry.register(PythonSandboxTool())
        self.tool_registry.register(SearchKnowledgeTool())

    def run(self, task: str) -> AgentState:
        return self.agent.run(task)