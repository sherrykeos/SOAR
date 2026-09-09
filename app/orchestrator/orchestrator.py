# Vajra pipeline

import re
import time
import uuid
from typing import Any, Dict, Optional

from app.models.manager import ModelExecutionResult, ModelManager
from app.tools.docx_creator import DOCXCreatorTool
from app.tools.pdf_creator import PDFCreatorTool
from app.tools.pdf_reader import PDFReaderTool
from app.tools.python_sandbox import PythonSandboxTool
from app.tools.read_file import ReadFileTool
from app.tools.registry import ToolRegistry
from app.tools.search_knowledge import SearchKnowledgeTool

from .action import ToolAction
from .agent import Agent
from .events import EventStage, EventStatus, ProgressEventEmitter
from .executor import Executor
from .planner import Planner
from .state import AgentState
from .task_classifier import TaskClassifier, TaskProfile


class Orchestrator:
    """
    Central Coordinator for SOAR Sovereign AI Agent.
    Orchestrates Task Classification, Adaptive Multi-Model Routing,
    Direct Answer Execution, Coding Pipelines, Multi-Step Agent Workflows,
    and Real Backend Progress Checkpoints.
    """

    def __init__(
        self,
        tool_registry: ToolRegistry | None = None,
        model_manager: ModelManager | None = None,
        task_classifier: TaskClassifier | None = None,
        emitter: ProgressEventEmitter | None = None,
        max_iterations: int = 5,
    ):
        self.model_manager = model_manager or ModelManager()
        self.classifier = task_classifier or TaskClassifier()
        self.emitter = emitter or ProgressEventEmitter()

        if tool_registry is None:
            self.tool_registry = ToolRegistry()
            self._register_default_tools()
        else:
            self.tool_registry = tool_registry

        self.planner = Planner(
            self.model_manager,
            tool_registry=self.tool_registry,
            emitter=self.emitter,
        )

        self.executor = Executor(
            tool_registry=self.tool_registry,
            emitter=self.emitter,
        )

        self.agent = Agent(
            planner=self.planner,
            executor=self.executor,
            max_iterations=max_iterations,
            emitter=self.emitter,
        )

    def _register_default_tools(self) -> None:
        self.tool_registry.register(ReadFileTool())
        self.tool_registry.register(PDFReaderTool())
        self.tool_registry.register(DOCXCreatorTool())
        self.tool_registry.register(PDFCreatorTool())
        self.tool_registry.register(PythonSandboxTool())
        self.tool_registry.register(SearchKnowledgeTool())

    def _extract_python_code(self, response_text: str) -> str:
        """Extracts python code blocks or returns full response text."""
        code_block = re.search(r"```(?:python)?\s*([\s\S]*?)\s*```", response_text, re.IGNORECASE)
        if code_block:
            return code_block.group(1).strip()
        return response_text.strip()

    def handle_direct_answer(
        self,
        task: str,
        profile: TaskProfile,
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes fast, single-turn direct answer mode.
        If requires_rag is True, retrieves local context from ChromaDB before answering.
        """
        citations = []
        if profile.requires_rag:
            try:
                search_action = ToolAction(
                    tool="search_knowledge",
                    arguments={"query": task, "top_k": 3},
                )
                search_res_dict = self.executor.execute_action(search_action, run_id=run_id)
                search_res = search_res_dict.get("result", {})

                context_chunks = []
                if isinstance(search_res, dict) and search_res.get("status") == "success":
                    for idx, r in enumerate(search_res.get("results", []), 1):
                        meta = r.get("metadata", {})
                        source = meta.get("filename") or meta.get("source_path") or "knowledge_base"
                        page = meta.get("page_number")
                        page_str = f", page {page}" if page is not None else ""
                        context_chunks.append(f"[{idx}] (Source: {source}{page_str}):\n{r.get('text', '')}")
                        citations.append(meta)

                rag_context = "\n\n".join(context_chunks)
                prompt = (
                    f"You are SOAR, a sovereign on-premise AI assistant.\n"
                    f"Answer the question accurately using ONLY the retrieved local context below.\n"
                    f"Include source citations (e.g. document name, page number) when applicable.\n\n"
                    f"RETRIEVED KNOWLEDGE CONTEXT:\n{rag_context}\n\n"
                    f"USER QUESTION:\n{task}\n\n"
                    f"ANSWER:"
                )
            except Exception as e:
                prompt = f"You are SOAR, a sovereign on-premise AI assistant.\n\nQuestion: {task}\n\nAnswer:"
        else:
            prompt = f"You are SOAR, a sovereign on-premise AI assistant.\n\nQuestion: {task}\n\nAnswer:"

        exec_result: ModelExecutionResult = self.model_manager.generate_with_routing(
            prompt,
            profile=profile,
            emitter=self.emitter,
            run_id=run_id,
        )

        if self.emitter:
            self.emitter.emit(
                stage=EventStage.COMPLETED,
                status=EventStatus.COMPLETED,
                message="Task completed",
                metadata={
                    "execution_mode": "direct_answer",
                    "model": exec_result.actual_model_id,
                },
                run_id=run_id,
            )

        return {
            "status": "success",
            "response": exec_result.response,
            "execution_mode": "direct_answer",
            "task_profile": profile.to_dict(),
            "citations": citations,
            "model": {
                "requested": exec_result.requested_model_id,
                "actual": exec_result.actual_model_id,
                "fallback_used": exec_result.fallback_used,
                "fallback_reason": exec_result.fallback_reason,
                "duration_seconds": exec_result.duration_seconds,
            },
            "events": self.emitter.get_event_dicts() if self.emitter else [],
        }

    def handle_coding(
        self,
        task: str,
        profile: TaskProfile,
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes dedicated Python coding path using qwen2.5-coder:1.5b.
        Optionally executes in python_sandbox if requested.
        """
        prompt = (
            f"You are SOAR's specialized Python coding assistant.\n"
            f"Provide clean, idiomatic, well-commented Python code for the following request.\n\n"
            f"TASK:\n{task}\n\n"
            f"PYTHON CODE:"
        )

        exec_result: ModelExecutionResult = self.model_manager.generate_with_routing(
            prompt,
            profile=profile,
            emitter=self.emitter,
            run_id=run_id,
        )

        extracted_code = self._extract_python_code(exec_result.response)
        sandbox_res = None
        final_response = exec_result.response

        # Execute in sandbox only if explicitly requested
        if profile.metadata.get("run_sandbox", False):
            sandbox_action = ToolAction(
                tool="python_sandbox",
                arguments={"code": extracted_code},
            )
            sandbox_exec = self.executor.execute_action(sandbox_action, run_id=run_id)
            if sandbox_exec.get("status") == "completed":
                sandbox_res = sandbox_exec.get("result")
                final_response += f"\n\n--- Sandbox Verification Output ---\n{sandbox_res}"
            else:
                sandbox_res = sandbox_exec.get("error", "Sandbox execution failed")
                final_response += f"\n\n--- Sandbox Verification Error ---\n{sandbox_res}"

        if self.emitter:
            self.emitter.emit(
                stage=EventStage.COMPLETED,
                status=EventStatus.COMPLETED,
                message="Task completed",
                metadata={
                    "execution_mode": "code",
                    "model": exec_result.actual_model_id,
                },
                run_id=run_id,
            )

        return {
            "status": "success",
            "response": final_response,
            "code": extracted_code,
            "sandbox_result": sandbox_res,
            "execution_mode": "code",
            "task_profile": profile.to_dict(),
            "model": {
                "requested": exec_result.requested_model_id,
                "actual": exec_result.actual_model_id,
                "fallback_used": exec_result.fallback_used,
                "fallback_reason": exec_result.fallback_reason,
                "duration_seconds": exec_result.duration_seconds,
            },
            "events": self.emitter.get_event_dicts() if self.emitter else [],
        }

    def process_task(self, task: str) -> Dict[str, Any]:
        """
        Main entry point for unified SOAR task processing.
        Classifies task, routes to optimal local model, and dispatches to
        direct answer, coding, or agent mode with real progress event emissions.
        """
        run_id = str(uuid.uuid4())
        if self.emitter:
            self.emitter.clear()
            self.emitter.emit(
                stage=EventStage.CLASSIFYING,
                status=EventStatus.STARTED,
                message="Classifying task",
                run_id=run_id,
            )

        profile = self.classifier.classify(task)

        if self.emitter:
            self.emitter.emit(
                stage=EventStage.CLASSIFYING,
                status=EventStatus.COMPLETED,
                message="Task classified",
                metadata={
                    "task_type": profile.task_type,
                    "complexity": profile.complexity,
                    "execution_mode": profile.execution_mode,
                    "requires_rag": profile.requires_rag,
                    "requires_vision": profile.requires_vision,
                    "requires_coding": profile.requires_coding,
                    "requires_tools": profile.requires_tools,
                },
                run_id=run_id,
            )
            self.emitter.emit(
                stage=EventStage.MODEL_SELECTING,
                status=EventStatus.STARTED,
                message="Selecting model",
                run_id=run_id,
            )

        if profile.execution_mode == "direct_answer":
            return self.handle_direct_answer(task, profile, run_id=run_id)
        elif profile.execution_mode == "code":
            return self.handle_coding(task, profile, run_id=run_id)
        else:
            # Multi-step Agent execution
            if self.emitter:
                self.emitter.emit(
                    stage=EventStage.MODEL_SELECTING,
                    status=EventStatus.COMPLETED,
                    message="Model selected — qwen3:1.7b",
                    metadata={"selected_model": "qwen3:1.7b", "routing_mode": "agent"},
                    run_id=run_id,
                )
            state = self.agent.run(task)
            return {
                "status": state.status,
                "response": "Agent workflow completed." if state.status == "completed" else "Agent encountered an error.",
                "execution_mode": "agent",
                "task_profile": profile.to_dict(),
                "agent_state": {
                    "iterations": state.iterations,
                    "observations": state.observations,
                    "results": state.results,
                },
                "model": {
                    "requested": "qwen3:1.7b",
                    "actual": "qwen3:1.7b",
                    "fallback_used": False,
                    "fallback_reason": None,
                },
                "events": self.emitter.get_event_dicts() if self.emitter else [],
            }

    def run(self, task: str) -> AgentState:
        """
        Coordinates execution and returns an AgentState.
        Maintains full backwards compatibility with all existing Agent unit tests.
        """
        run_id = str(uuid.uuid4())
        profile = self.classifier.classify(task)

        if profile.execution_mode == "agent":
            if self.emitter:
                self.emitter.clear()
                self.emitter.emit(
                    stage=EventStage.CLASSIFYING,
                    status=EventStatus.STARTED,
                    message="Classifying task",
                    run_id=run_id,
                )
                self.emitter.emit(
                    stage=EventStage.CLASSIFYING,
                    status=EventStatus.COMPLETED,
                    message="Task classified",
                    metadata=profile.to_dict(),
                    run_id=run_id,
                )
                self.emitter.emit(
                    stage=EventStage.MODEL_SELECTING,
                    status=EventStatus.STARTED,
                    message="Selecting model",
                    run_id=run_id,
                )
                self.emitter.emit(
                    stage=EventStage.MODEL_SELECTING,
                    status=EventStatus.COMPLETED,
                    message="Model selected — qwen3:1.7b",
                    metadata={"selected_model": "qwen3:1.7b", "routing_mode": "agent"},
                    run_id=run_id,
                )
            state = self.agent.run(task)
            if self.emitter:
                state.events = self.emitter.get_events()
            return state

        # For direct answer / code, execute and wrap outcome into AgentState
        proc_result = self.process_task(task)
        state = AgentState(
            task=task,
            run_id=run_id,
            max_iterations=self.agent.max_iterations,
        )
        state.iterations = 1
        state.status = "completed" if proc_result.get("status") == "success" else "error"
        state.results.append(
            {
                "status": "completed" if proc_result.get("status") == "success" else "error",
                "response": proc_result.get("response", ""),
                "execution_mode": proc_result.get("execution_mode"),
                "model": proc_result.get("model", {}),
            }
        )
        state.observations.append(
            {
                "iteration": 1,
                "tool": "direct_execution",
                "status": "completed",
                "result": proc_result.get("response", ""),
            }
        )
        if self.emitter:
            state.events = self.emitter.get_events()
        return state