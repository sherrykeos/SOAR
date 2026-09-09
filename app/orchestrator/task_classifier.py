import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TaskProfile:
    """
    Structured profile describing the classification, complexity,
    resource requirements, and execution mode of a user task.
    """

    task_type: str  # "question_answering", "reasoning", "coding", "document", "multimodal", "calculation", "general"
    complexity: str  # "simple", "medium", "hard"
    requires_rag: bool = False
    requires_vision: bool = False
    requires_coding: bool = False
    requires_tools: bool = False
    execution_mode: str = "direct_answer"  # "direct_answer", "code", "agent"
    original_task: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TaskClassifier:
    """
    Lightweight, deterministic task classifier for SOAR.
    Analyzes tasks using deterministic heuristics, regex patterns, and keyword signals
    with zero latency overhead (100% on-premise, air-gapped).
    Can be seamlessly upgraded to an LLM-based classifier in future milestones.
    """

    # Image / Vision patterns
    VISION_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}
    VISION_KEYWORDS = [
        "image",
        "photo",
        "photograph",
        "picture",
        "scanned",
        "diagram",
        "chart",
        "visual",
        "ocr",
        "snapshot",
    ]

    # Python Coding patterns
    CODING_KEYWORDS = [
        "write a python",
        "python function",
        "python script",
        "python code",
        "python program",
        "write code",
        "write python",
        "code a python",
        "implement a python",
        "create a python function",
        "def ",
        "class ",
        "bug in python",
        "fix python",
        "refactor python",
        "python algorithm",
        "sum three numbers",
        "add three numbers",
        "sum of numbers",
    ]

    # Explicit sandbox execution request
    SANDBOX_KEYWORDS = [
        "test the code",
        "run the code",
        "verify the code",
        "execute the code",
        "run in sandbox",
        "write and test",
        "code and execute",
        "execute python",
    ]

    # Multi-step / Document / Tool workflows
    DOCUMENT_KEYWORDS = [
        "create a docx",
        "create a pdf",
        "create docx",
        "create pdf",
        "make docx",
        "make a docx",
        "make pdf",
        "make a pdf",
        "generate docx",
        "generate pdf",
        "approval note",
        "approval_note",
        "inspection report",
        "inspection_report",
        "inputs/",
        "outputs/",
        "read_file",
        "pdf_reader",
        "docx_creator",
        "pdf_creator",
    ]

    # Knowledge Base / RAG domain signals
    RAG_KEYWORDS = [
        "boiler",
        "boiler b-4",
        "v-12",
        "sop-",
        "sop ",
        "safety manual",
        "operating pressure",
        "pressure limit",
        "safety requirement",
        "operating limit",
        "turbine vibration",
        "inspection protocol",
        "knowledge base",
        "policy document",
        "operating manual",
        "regulations",
    ]

    # Calculation signals
    CALC_KEYWORDS = [
        "calculate",
        "compute",
        "solve",
        "math",
        "what is 2 + 2",
        "2 + 2",
    ]

    # Hard reasoning signals
    HARD_REASONING_KEYWORDS = [
        "root cause",
        "deep analysis",
        "diagnose why",
        "explain why a pressure vessel",
        "failure mode analysis",
        "trade-off analysis",
        "compare and contrast",
        "multi-factor analysis",
        "troubleshoot systemic",
    ]

    def classify(self, task: str) -> TaskProfile:
        """
        Classifies a user task string into a structured TaskProfile.
        """
        task_clean = task.strip()
        task_lower = task_clean.lower()

        # Extract file paths mentioned in task
        file_matches = re.findall(r"[\w\-\./\\]+\.[a-zA-Z0-9]+", task_clean)
        has_image_file = any(
            any(f.lower().endswith(ext) for ext in self.VISION_EXTENSIONS)
            for f in file_matches
        )
        has_doc_file = any(
            any(f.lower().endswith(ext) for ext in {".pdf", ".docx", ".pptx", ".txt"})
            for f in file_matches
        )

        metadata: Dict[str, Any] = {
            "file_paths": file_matches,
        }

        # -------------------------------------------------------------
        # 1. Vision / Multimodal Classification
        # -------------------------------------------------------------
        has_vision_kw = any(kw in task_lower for kw in self.VISION_KEYWORDS)
        if has_image_file or has_vision_kw:
            # Check if it's a combined document generation task
            has_doc_create = any(
                kw in task_lower
                for kw in ["create a docx", "create a pdf", "approval note", "generate docx", "generate pdf", "make docx", "make pdf"]
            )
            if has_doc_create:
                return TaskProfile(
                    task_type="document",
                    complexity="hard",
                    requires_rag=False,
                    requires_vision=True,
                    requires_coding=False,
                    requires_tools=True,
                    execution_mode="agent",
                    original_task=task_clean,
                    metadata=metadata,
                )
            return TaskProfile(
                task_type="multimodal",
                complexity="simple",
                requires_rag=False,
                requires_vision=True,
                requires_coding=False,
                requires_tools=False,
                execution_mode="direct_answer",
                original_task=task_clean,
                metadata=metadata,
            )

        # -------------------------------------------------------------
        # 2. Multi-step Document / Agent Workflows
        # -------------------------------------------------------------
        has_doc_kw = any(kw in task_lower for kw in self.DOCUMENT_KEYWORDS)
        # Check for explicit document creation action (e.g. "make docx", "create pdf", "save as docx")
        has_doc_intent = bool(
            re.search(
                r"\b(make|create|generate|write|build|save|export|produce)\b.*?\b(docx|pdf|document|word document|word doc|doc file|pdf file|docx file)\b",
                task_lower,
            )
        )
        # Check for multi-action chaining (e.g. "read ... and create ...", "analyze ... against ... and create ...")
        is_multi_step = bool(
            re.search(r"\bread\b.+\b(create|generate|write|make)\b", task_lower)
            or re.search(r"\banalyze\b.+\b(create|generate|write|make)\b", task_lower)
            or re.search(r"\bsearch\b.+\b(create|generate|write|make)\b", task_lower)
            or (has_doc_kw and any(kw in task_lower for kw in ["create", "make", "generate", "write", "approval note", "note", "summarize", "docx", "pdf"]))
            or has_doc_intent
        )

        if is_multi_step or has_doc_intent or (has_doc_file and has_doc_kw):
            requires_rag = any(kw in task_lower for kw in self.RAG_KEYWORDS)
            is_complex = "against our safety manual" in task_lower or "analyze" in task_lower or requires_rag
            return TaskProfile(
                task_type="document",
                complexity="hard" if is_complex else "medium",
                requires_rag=requires_rag,
                requires_vision=False,
                requires_coding=False,
                requires_tools=True,
                execution_mode="agent",
                original_task=task_clean,
                metadata=metadata,
            )

        # -------------------------------------------------------------
        # 3. Python Coding Classification
        # -------------------------------------------------------------
        has_coding_kw = any(kw in task_lower for kw in self.CODING_KEYWORDS) or "python" in task_lower
        if has_coding_kw:
            run_sandbox = any(kw in task_lower for kw in self.SANDBOX_KEYWORDS)
            metadata["run_sandbox"] = run_sandbox
            return TaskProfile(
                task_type="coding",
                complexity="simple",
                requires_rag=False,
                requires_vision=False,
                requires_coding=True,
                requires_tools=run_sandbox,
                execution_mode="code",
                original_task=task_clean,
                metadata=metadata,
            )

        # -------------------------------------------------------------
        # 4. Calculation / Math
        # -------------------------------------------------------------
        has_calc_kw = any(kw in task_lower for kw in self.CALC_KEYWORDS) or bool(
            re.search(r"^\s*what\s+is\s+\d+\s*[\+\-\*\/]\s*\d+\s*\??$", task_lower)
        )
        if has_calc_kw:
            return TaskProfile(
                task_type="calculation",
                complexity="simple",
                requires_rag=False,
                requires_vision=False,
                requires_coding=False,
                requires_tools=False,
                execution_mode="direct_answer",
                original_task=task_clean,
                metadata=metadata,
            )

        # -------------------------------------------------------------
        # 5. Knowledge Base / RAG Question Answering
        # -------------------------------------------------------------
        has_rag_kw = any(kw in task_lower for kw in self.RAG_KEYWORDS)
        if has_rag_kw:
            return TaskProfile(
                task_type="question_answering",
                complexity="simple",
                requires_rag=True,
                requires_vision=False,
                requires_coding=False,
                requires_tools=False,
                execution_mode="direct_answer",
                original_task=task_clean,
                metadata=metadata,
            )

        # -------------------------------------------------------------
        # 6. Hard Reasoning vs Medium / Simple General
        # -------------------------------------------------------------
        has_hard_reasoning = any(kw in task_lower for kw in self.HARD_REASONING_KEYWORDS)
        if has_hard_reasoning:
            return TaskProfile(
                task_type="reasoning",
                complexity="hard",
                requires_rag=False,
                requires_vision=False,
                requires_coding=False,
                requires_tools=False,
                execution_mode="direct_answer",
                original_task=task_clean,
                metadata=metadata,
            )

        # Check medium reasoning / general explanation
        if any(kw in task_lower for kw in ["explain", "why", "how does", "compare", "describe"]):
            return TaskProfile(
                task_type="reasoning",
                complexity="medium",
                requires_rag=False,
                requires_vision=False,
                requires_coding=False,
                requires_tools=False,
                execution_mode="direct_answer",
                original_task=task_clean,
                metadata=metadata,
            )

        # -------------------------------------------------------------
        # 7. Default Simple General Question Answering
        # -------------------------------------------------------------
        return TaskProfile(
            task_type="general",
            complexity="simple",
            requires_rag=False,
            requires_vision=False,
            requires_coding=False,
            requires_tools=False,
            execution_mode="direct_answer",
            original_task=task_clean,
            metadata=metadata,
        )
