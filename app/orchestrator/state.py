import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class TaskContext:
    """
    Preserves the user's original task verbatim as the single source of truth,
    and stores derived path metadata to guide the planner with exact user paths.
    """
    original_task: str
    detected_paths: list[str] = field(default_factory=list)
    input_paths: list[str] = field(default_factory=list)
    output_paths: list[str] = field(default_factory=list)

    @classmethod
    def from_task(cls, task: str) -> "TaskContext":
        if not task:
            return cls(original_task="")

        # Generic pattern for file paths (e.g. inputs/inspection_report.pdf, outputs/approval_note.docx, file.txt)
        # Matches paths with extension or folder prefixes
        pattern = r"['\"`]?(?:[a-zA-Z0-9_\-\./\\]+[\\/])?[a-zA-Z0-9_\-]+\.[a-zA-Z0-9]{2,5}['\"`]?"
        matches = re.findall(pattern, task)
        
        cleaned_paths: list[str] = []
        for m in matches:
            clean = m.strip("'\"` ").replace("\\", "/")
            if clean and clean not in cleaned_paths:
                cleaned_paths.append(clean)

        input_candidates = []
        output_candidates = []

        task_lower = task.lower()
        for path in cleaned_paths:
            path_lower = path.lower()
            if "input" in path_lower or "in/" in path_lower or "read" in task_lower:
                if not ("output" in path_lower or "create" in path_lower and path_lower in task_lower[task_lower.find("create"):]):
                    input_candidates.append(path)
            if "output" in path_lower or "out/" in path_lower or "save" in task_lower or "create" in task_lower or "as" in task_lower:
                output_candidates.append(path)

        # Fallback if unassigned
        if not input_candidates and cleaned_paths:
            input_candidates = [cleaned_paths[0]]
        if not output_candidates and len(cleaned_paths) > 1:
            output_candidates = cleaned_paths[1:]

        return cls(
            original_task=task,
            detected_paths=cleaned_paths,
            input_paths=input_candidates,
            output_paths=output_candidates,
        )


@dataclass
class AgentState:
    task: str
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    plan: list[Any] = field(default_factory=list)
    current_step: int = 0
    results: list[Any] = field(default_factory=list)
    observations: list[dict[str, Any]] = field(default_factory=list)
    events: list[Any] = field(default_factory=list)
    iterations: int = 0
    max_iterations: int = 5
    status: str = "pending"
    context: Optional[TaskContext] = None
    failure_fingerprints: list[dict[str, Any]] = field(default_factory=list)