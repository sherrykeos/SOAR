# Vajra pipeline

import logging
import mimetypes
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.models.manager import ModelExecutionResult, ModelManager
from app.config import resolve_project_path
from app.tools.docx_creator import DOCXCreatorTool
from app.tools.pdf_creator import PDFCreatorTool
from app.tools.pdf_reader import PDFReaderTool
from app.tools.python_sandbox import PythonSandboxTool
from app.tools.read_file import ReadFileTool
from app.tools.registry import ToolRegistry
from app.tools.search_knowledge import SearchKnowledgeTool

from .agent import Agent, AgentState
from .events import EventStage, EventStatus, ProgressEventEmitter
from .execution import Executor, ToolAction
from .planning import Planner
from .routing import TaskClassifier, TaskProfile

logger = logging.getLogger(__name__)


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
        max_iterations: Optional[int] = None,
        config: Optional[Any] = None,
    ):
        from app.config import SOARConfig, get_config

        self.config: SOARConfig = config or get_config()
        self.model_manager = model_manager or ModelManager(config=self.config)
        self.classifier = task_classifier or TaskClassifier()
        self.emitter = emitter or ProgressEventEmitter()

        eff_max_iterations = (
            max_iterations
            if max_iterations is not None
            else getattr(self.config.agent, "max_iterations", 5)
        )

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
            max_iterations=eff_max_iterations,
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
        model_id: Optional[str] = None,
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
            model_id=model_id,
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
            "run_id": run_id,
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
            "events": self.emitter.get_events_for_run(run_id) if (self.emitter and run_id) else (self.emitter.get_event_dicts() if self.emitter else []),
        }

    def handle_coding(
        self,
        task: str,
        profile: TaskProfile,
        run_id: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes dedicated Python coding path using qwen2.5-coder:1.5b (or explicit model_id).
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
            model_id=model_id,
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
            "run_id": run_id,
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
            "events": self.emitter.get_events_for_run(run_id) if (self.emitter and run_id) else (self.emitter.get_event_dicts() if self.emitter else []),
        }

    def _resolve_uploaded_files(self, file_ids: List[str]) -> str:
        """
        Resolves uploaded file_ids to their real storage paths via LocalFileStorage,
        then directly extracts the content (PDF text, plain text) and injects it
        into the task prompt as explicit document context.

        For PDFs: uses PDFReaderTool to extract text directly.
        For text files: reads content directly.
        This avoids passing absolute paths to the LLM, which it cannot reliably reproduce.
        """
        from app.api.dependencies import get_storage
        storage = get_storage()
        sections: List[str] = []

        for fid in file_ids:
            fid = fid.strip()
            if not fid:
                continue
            try:
                path = storage.get_path(fid)
                meta = storage.get_metadata(fid)
                original_name = meta.original_filename if meta else path.name
                suffix = path.suffix.lower()

                if suffix == ".pdf":
                    # Extract text directly using the existing PDFReaderTool
                    reader = PDFReaderTool()
                    extracted = reader.execute(file_path=str(path))
                    if extracted.startswith("Error:"):
                        logger.warning(f"PDF extraction failed for '{original_name}': {extracted}")
                        sections.append(
                            f"[Uploaded file: {original_name}]\n"
                            f"Unable to read this PDF locally: {extracted}\n"
                        )
                    else:
                        # Truncate very large docs to avoid blowing the context window
                        max_chars = 8000
                        truncated = extracted[:max_chars]
                        if len(extracted) > max_chars:
                            truncated += f"\n... [truncated — {len(extracted) - max_chars} additional characters not shown]"
                        sections.append(
                            f"[Uploaded document: {original_name}]\n"
                            f"{truncated}\n"
                        )
                elif suffix in (".txt", ".md", ".csv", ".log", ".json", ".xml", ".html"):
                    content = path.read_text(encoding="utf-8", errors="replace")
                    max_chars = 8000
                    truncated = content[:max_chars]
                    if len(content) > max_chars:
                        truncated += f"\n... [truncated]"
                    sections.append(
                        f"[Uploaded file: {original_name}]\n"
                        f"{truncated}\n"
                    )
                else:
                    # For binary/unsupported types, note the file name only
                    sections.append(
                        f"[Uploaded file: {original_name} (type: {suffix or 'unknown'}) — binary content not shown]\n"
                    )
            except Exception as e:
                logger.warning(f"Could not resolve uploaded file_id '{fid}': {e}")

        if not sections:
            return ""

        header = (
            "=== UPLOADED DOCUMENT CONTEXT ===\n"
            "The following document(s) were uploaded by the user. "
            "Use this content to answer the question below.\n\n"
        )
        return header + "\n".join(sections) + "=== END DOCUMENT CONTEXT ===\n\n"


    def _register_generated_files(self, observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Scans agent observations for successfully created documents (pdf_creator/docx_creator),
        verifies the output file physically exists, registers it through LocalFileStorage,
        and returns a list of {file_id, filename, mime_type} dicts for the API response.
        """
        from app.api.dependencies import get_storage
        storage = get_storage()
        generated: List[Dict[str, Any]] = []
        seen_paths: set = set()

        for obs in observations:
            tool = obs.get("tool")
            if tool not in ("pdf_creator", "docx_creator"):
                continue
            if obs.get("status") != "completed":
                continue

            args = obs.get("arguments", {})
            output_path = args.get("output_path") or args.get("file_path") or args.get("path")
            if not output_path or output_path in seen_paths:
                continue
            seen_paths.add(output_path)

            target = resolve_project_path(output_path)

            if not target.exists() or not target.is_file():
                logger.warning(f"Generated file not found at '{output_path}', skipping registration.")
                continue

            try:
                mime_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
                meta = storage.save(
                    content=target,
                    filename=target.name,
                    content_type=mime_type,
                )
                generated.append({
                    "file_id": meta.file_id,
                    "filename": meta.original_filename,
                    "mime_type": mime_type,
                })
                logger.info(f"Registered generated file '{target.name}' as file_id={meta.file_id}")
            except Exception as e:
                logger.warning(f"Failed to register generated file '{output_path}': {e}")

        return generated

    def process_task(
        self,
        task: str,
        run_id: Optional[str] = None,
        model_id: Optional[str] = None,
        attached_file_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point for unified SOAR task processing.
        Classifies task, routes to optimal local model (or explicit override), and dispatches to
        direct answer, coding, or agent mode with real progress event emissions.
        """
        if model_id:
            try:
                adapter = self.model_manager.registry.get(model_id)
                if not adapter.is_available():
                    raise ValueError(f"Requested model '{model_id}' is offline or not installed in Ollama.")
            except KeyError:
                raise ValueError(f"Requested model '{model_id}' is not configured in SOAR.")

        # Resolve uploaded files and inject their real storage paths into the prompt
        if attached_file_ids:
            file_context = self._resolve_uploaded_files(attached_file_ids)
            if file_context:
                task = file_context + "\n" + task

        active_run_id = run_id or str(uuid.uuid4())
        if self.emitter:
            self.emitter.emit(
                stage=EventStage.CLASSIFYING,
                status=EventStatus.STARTED,
                message="Classifying task",
                run_id=active_run_id,
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
                run_id=active_run_id,
            )
            self.emitter.emit(
                stage=EventStage.MODEL_SELECTING,
                status=EventStatus.STARTED,
                message="Selecting model",
                run_id=active_run_id,
            )

        if profile.execution_mode == "direct_answer":
            return self.handle_direct_answer(task, profile, run_id=active_run_id, model_id=model_id)
        elif profile.execution_mode == "code":
            return self.handle_coding(task, profile, run_id=active_run_id, model_id=model_id)
        else:
            # Multi-step Agent execution
            # Determine which model the agent will actually use for planning/generation
            chosen_agent_model = model_id or self.model_manager.default_model_name
            if self.emitter:
                self.emitter.emit(
                    stage=EventStage.MODEL_SELECTING,
                    status=EventStatus.COMPLETED,
                    message=f"Model selected — {chosen_agent_model}",
                    metadata={"selected_model": chosen_agent_model, "routing_mode": "manual" if model_id else "agent"},
                    run_id=active_run_id,
                )
            state = self.agent.run(task, run_id=active_run_id, model_id=model_id)

            # Resolve actual model used: prefer what the planner's generate() routed to
            # model_manager.generate() uses route_by_id (if model_id) or route() (if None)
            if model_id:
                actual_agent_model = model_id
            else:
                try:
                    routed = self.model_manager.router.route(task_type="general")
                    actual_agent_model = routed.model_id
                except Exception:
                    actual_agent_model = chosen_agent_model

            # Register any generated files (pdf/docx) into LocalFileStorage. This
            # is deliberately best-effort: document creation already succeeded,
            # so storage indexing must not convert a successful task into a 500.
            try:
                generated_files = self._register_generated_files(state.observations)
            except Exception as e:
                logger.exception("Generated file registration failed after task completion: %s", e)
                generated_files = []

            # Synthesize user-facing response from agent observations (deduplicating created documents)
            seen_files = set()
            response_chunks = []
            for obs in state.observations:
                tool = obs.get("tool")
                args = obs.get("arguments", {})
                res = obs.get("result", "")
                if tool in ("pdf_creator", "docx_creator"):
                    out_path = args.get("output_path", "")
                    if out_path and out_path in seen_files:
                        continue
                    if out_path:
                        seen_files.add(out_path)
                    title = args.get("title", "")
                    content = args.get("content", "")
                    if title:
                        response_chunks.append(f"## {title}\n\n{content}")
                    elif content:
                        response_chunks.append(content)
                    if out_path:
                        response_chunks.append(f"\n> 📄 **Document Saved:** `{out_path}` ({res})")
                elif tool == "python_sandbox":
                    code = args.get("code", "")
                    if code:
                        response_chunks.append(f"```python\n{code}\n```")
                    if res:
                        response_chunks.append(f"**Output:**\n```\n{res}\n```")
                elif tool == "search_knowledge":
                    if isinstance(res, dict) and res.get("status") == "success":
                        results = res.get("results", [])
                        if results:
                            response_chunks.append(f"**Retrieved {len(results)} relevant knowledge source(s).**")
                elif res and isinstance(res, str) and not res.startswith("Successfully created"):
                    response_chunks.append(res)

            if response_chunks:
                agent_response = "\n\n".join(response_chunks)
            elif state.status == "completed":
                agent_response = "Agent workflow completed successfully."
            else:
                agent_response = "Agent encountered an error during workflow execution."

            return {
                "run_id": active_run_id,
                "status": state.status,
                "response": agent_response,
                "execution_mode": "agent",
                "task_profile": profile.to_dict(),
                "agent_state": {
                    "iterations": state.iterations,
                    "observations": state.observations,
                    "results": state.results,
                },
                "model": {
                    "requested": chosen_agent_model,
                    "actual": actual_agent_model,
                    "fallback_used": False,
                    "fallback_reason": None,
                },
                "generated_files": generated_files,
                "events": self.emitter.get_events_for_run(active_run_id) if (self.emitter and active_run_id) else (self.emitter.get_event_dicts() if self.emitter else []),
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
            state = self.agent.run(task, run_id=run_id)
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
