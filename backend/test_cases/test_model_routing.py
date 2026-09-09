import json
import tempfile
import unittest
from pathlib import Path

from app.models.adapter import ModelCapability
from app.models.manager import ModelManager
from app.models.mock import MockModel
from app.models.registry import ModelRegistry
from app.models.router import ModelRouter
from app.orchestrator import Orchestrator
from app.orchestrator.routing import TaskClassifier, TaskProfile
from app.tools.base import BaseTool
from app.tools.registry import ToolRegistry


class SlowTimingOutModel(MockModel):
    """Mock model that simulates timeout on execution."""

    def generate(self, prompt: str, *, think: bool = False, timeout: float = 15.0, **kwargs):
        raise TimeoutError(f"Ollama model '{self._model_id}' timed out after {timeout} seconds.")


class CrashingInferenceModel(MockModel):
    """Mock model that simulates runtime inference crash."""

    def generate(self, prompt: str, *, think: bool = False, **kwargs):
        raise RuntimeError("CUDA device side assert triggered in model.")


class DummySearchKnowledgeTool(BaseTool):
    """Deterministic search tool for testing direct answer RAG routing."""

    @property
    def name(self) -> str:
        return "search_knowledge"

    @property
    def description(self) -> str:
        return "Search knowledge base."

    def execute(self, **kwargs):
        return {
            "status": "success",
            "query": kwargs.get("query", ""),
            "count": 1,
            "results": [
                {
                    "text": "Boiler B-4 approved operating pressure is 120-145 PSI.",
                    "score": 0.95,
                    "metadata": {
                        "filename": "boiler_manual.pdf",
                        "page_number": 14,
                    },
                }
            ],
        }


class DummyPythonSandboxTool(BaseTool):
    """Deterministic sandbox tool for testing coding sandbox execution."""

    @property
    def name(self) -> str:
        return "python_sandbox"

    @property
    def description(self) -> str:
        return "Executes Python code in sandbox."

    def execute(self, **kwargs):
        code = kwargs.get("code", "")
        return f"Status: Success (Executed {len(code)} characters)"


class TestModelRouting(unittest.TestCase):
    """
    Comprehensive test suite for Adaptive Model Routing, Model Availability Checks,
    Timeout Fallbacks, Direct Answer Mode, and Coding Pipelines.
    """

    def setUp(self):
        # Build local mock model pool representing the 4 SOAR models
        self.mock_qwen3 = MockModel(
            model_id="qwen3:1.7b",
            capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
            priority=10,
            fixed_response="Answer from fast qwen3:1.7b model.",
        )
        self.mock_qwen2_4b = MockModel(
            model_id="qwen2:4b",
            capabilities={ModelCapability.REASONING},
            priority=20,
            fixed_response="Deep reasoning response from qwen2:4b.",
        )
        self.mock_coder = MockModel(
            model_id="qwen2.5-coder:1.5b",
            capabilities={ModelCapability.CODING},
            priority=15,
            fixed_response="```python\ndef add_three(a, b, c):\n    return a + b + c\n```",
        )
        self.mock_vision = MockModel(
            model_id="qwen2.5vl:3b",
            capabilities={ModelCapability.VISION},
            priority=15,
            fixed_response="Visual scene description from qwen2.5vl:3b.",
        )

        self.registry = ModelRegistry()
        self.registry.register(self.mock_qwen3)
        self.registry.register(self.mock_qwen2_4b)
        self.registry.register(self.mock_coder)
        self.registry.register(self.mock_vision)

        self.router = ModelRouter(self.registry, default_model_id="qwen3:1.7b", hard_model_timeout=15.0)
        self.manager = ModelManager(model_registry=self.registry, model_router=self.router, default_model_name="qwen3:1.7b")
        self.classifier = TaskClassifier()

    # -------------------------------------------------------------
    # 1. Routing by Task Profile
    # -------------------------------------------------------------
    def test_route_simple_general_to_qwen3(self):
        profile = self.classifier.classify("What is the capital of France?")
        decision = self.router.route_task(profile)
        self.assertEqual(decision.requested_model_id, "qwen3:1.7b")
        self.assertEqual(decision.selected_model.model_id, "qwen3:1.7b")
        self.assertFalse(decision.fallback_used)

    def test_route_coding_to_qwen_coder(self):
        profile = self.classifier.classify("Write a Python function to sum three numbers.")
        decision = self.router.route_task(profile)
        self.assertEqual(decision.requested_model_id, "qwen2.5-coder:1.5b")
        self.assertEqual(decision.selected_model.model_id, "qwen2.5-coder:1.5b")
        self.assertFalse(decision.fallback_used)

    def test_route_vision_to_qwen_vl(self):
        profile = self.classifier.classify("What does this image show?")
        decision = self.router.route_task(profile)
        self.assertEqual(decision.requested_model_id, "qwen2.5vl:3b")
        self.assertEqual(decision.selected_model.model_id, "qwen2.5vl:3b")
        self.assertFalse(decision.fallback_used)

    def test_route_hard_reasoning_to_qwen2_4b(self):
        profile = self.classifier.classify("Explain why a pressure vessel might experience abnormal pressure.")
        decision = self.router.route_task(profile)
        self.assertEqual(decision.requested_model_id, "qwen2:4b")
        self.assertEqual(decision.selected_model.model_id, "qwen2:4b")
        self.assertEqual(decision.timeout_seconds, 15.0)
        self.assertFalse(decision.fallback_used)

    def test_route_medium_reasoning_prefers_fast_model(self):
        profile = self.classifier.classify("Explain how a heat exchanger works.")
        decision = self.router.route_task(profile)
        # SPEED > ACCURACY for MVP -> routes to fast model qwen3:1.7b
        self.assertEqual(decision.requested_model_id, "qwen3:1.7b")
        self.assertEqual(decision.selected_model.model_id, "qwen3:1.7b")

    # -------------------------------------------------------------
    # 2. Unavailable Model Local Fallback
    # -------------------------------------------------------------
    def test_unavailable_model_falls_back_to_qwen3(self):
        # Create a registry where qwen2:4b is marked unavailable
        reg = ModelRegistry()
        reg.register(self.mock_qwen3)
        reg.register(
            MockModel(
                model_id="qwen2:4b",
                capabilities={ModelCapability.REASONING},
                available=False,
            )
        )
        router = ModelRouter(reg, default_model_id="qwen3:1.7b")

        profile = TaskProfile(
            task_type="reasoning",
            complexity="hard",
            original_task="Hard diagnostic question",
        )
        decision = router.route_task(profile)
        self.assertEqual(decision.requested_model_id, "qwen2:4b")
        self.assertEqual(decision.selected_model.model_id, "qwen3:1.7b")
        self.assertTrue(decision.fallback_used)
        self.assertEqual(decision.fallback_reason, "requested model unavailable")

    # -------------------------------------------------------------
    # 3. Timeout and Inference Error Fallbacks
    # -------------------------------------------------------------
    def test_timeout_fallback_to_fast_model(self):
        # Register a slow timing-out model as qwen2:4b
        slow_registry = ModelRegistry()
        slow_registry.register(self.mock_qwen3)
        slow_registry.register(
            SlowTimingOutModel(
                model_id="qwen2:4b",
                capabilities={ModelCapability.REASONING},
            )
        )
        slow_router = ModelRouter(slow_registry, default_model_id="qwen3:1.7b", hard_model_timeout=15.0)
        slow_manager = ModelManager(model_registry=slow_registry, model_router=slow_router)

        profile = TaskProfile(
            task_type="reasoning",
            complexity="hard",
            original_task="Explain abnormal pressure",
        )

        res = slow_manager.generate_with_routing("Explain abnormal pressure", profile=profile)
        self.assertEqual(res.requested_model_id, "qwen2:4b")
        self.assertEqual(res.actual_model_id, "qwen3:1.7b")
        self.assertTrue(res.fallback_used)
        self.assertEqual(res.fallback_reason, "timeout")
        self.assertIn("Answer from fast qwen3:1.7b", res.response)

    def test_inference_error_fallback_to_fast_model(self):
        # Register a crashing model
        crash_registry = ModelRegistry()
        crash_registry.register(self.mock_qwen3)
        crash_registry.register(
            CrashingInferenceModel(
                model_id="qwen2:4b",
                capabilities={ModelCapability.REASONING},
            )
        )
        crash_router = ModelRouter(crash_registry, default_model_id="qwen3:1.7b")
        crash_manager = ModelManager(model_registry=crash_registry, model_router=crash_router)

        profile = TaskProfile(
            task_type="reasoning",
            complexity="hard",
            original_task="Explain abnormal pressure",
        )

        res = crash_manager.generate_with_routing("Explain abnormal pressure", profile=profile)
        self.assertEqual(res.requested_model_id, "qwen2:4b")
        self.assertEqual(res.actual_model_id, "qwen3:1.7b")
        self.assertTrue(res.fallback_used)
        self.assertIn("inference error", res.fallback_reason)
        self.assertIn("Answer from fast qwen3:1.7b", res.response)

    # -------------------------------------------------------------
    # 4. Orchestrator Direct Answer Mode (Simple Q&A & Simple RAG)
    # -------------------------------------------------------------
    def test_orchestrator_direct_answer_simple_question(self):
        orch = Orchestrator(model_manager=self.manager)
        res = orch.process_task("What is the capital of France?")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["execution_mode"], "direct_answer")
        self.assertEqual(res["model"]["actual"], "qwen3:1.7b")
        self.assertIn("qwen3:1.7b", res["response"])

    def test_orchestrator_direct_answer_rag_question(self):
        tool_reg = ToolRegistry()
        tool_reg.register(DummySearchKnowledgeTool())

        orch = Orchestrator(tool_registry=tool_reg, model_manager=self.manager)
        res = orch.process_task("What is the pressure limit for Boiler B-4?")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["execution_mode"], "direct_answer")
        self.assertEqual(res["task_profile"]["requires_rag"], True)
        self.assertTrue(len(res["citations"]) > 0)
        self.assertEqual(res["citations"][0]["filename"], "boiler_manual.pdf")

    # -------------------------------------------------------------
    # 5. Orchestrator Coding Mode with & without Sandbox
    # -------------------------------------------------------------
    def test_orchestrator_coding_without_sandbox(self):
        orch = Orchestrator(model_manager=self.manager)
        res = orch.process_task("Write a Python function to add three numbers.")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["execution_mode"], "code")
        self.assertEqual(res["model"]["actual"], "qwen2.5-coder:1.5b")
        self.assertIn("def add_three", res["code"])
        self.assertIsNone(res["sandbox_result"])

    def test_orchestrator_coding_with_explicit_sandbox(self):
        tool_reg = ToolRegistry()
        tool_reg.register(DummyPythonSandboxTool())

        orch = Orchestrator(tool_registry=tool_reg, model_manager=self.manager)
        res = orch.process_task("Write and test a Python function that adds three numbers.")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["execution_mode"], "code")
        self.assertEqual(res["model"]["actual"], "qwen2.5-coder:1.5b")
        self.assertIsNotNone(res["sandbox_result"])
        self.assertIn("Status: Success", res["sandbox_result"])

    # -------------------------------------------------------------
    # 6. Orchestrator Agent Mode for Complex Workflows
    # -------------------------------------------------------------
    def test_orchestrator_agent_mode_for_complex_document(self):
        class SequencePlanResponder:
            def __init__(self):
                self.count = 0

            def __call__(self, prompt: str) -> str:
                self.count += 1
                return json.dumps({
                    "status": "complete",
                    "thought": "Finished analysis.",
                    "steps": [],
                })

        agent_mock = MockModel(
            model_id="agent-model",
            capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
            response_fn=SequencePlanResponder(),
        )
        reg = ModelRegistry()
        reg.register(agent_mock)
        mgr = ModelManager(model_registry=reg, model_router=ModelRouter(reg, default_model_id="agent-model"))

        orch = Orchestrator(model_manager=mgr)
        res = orch.process_task("Read inputs/inspection_report.pdf and create outputs/approval_note.docx")
        self.assertEqual(res["execution_mode"], "agent")
        self.assertEqual(res["status"], "completed")


if __name__ == "__main__":
    unittest.main()
