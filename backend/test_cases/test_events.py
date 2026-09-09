import unittest
from unittest.mock import MagicMock, patch

from app.models.adapter import ModelCapability
from app.models.manager import ModelExecutionResult, ModelManager
from app.models.mock import MockModel
from app.models.registry import ModelRegistry
from app.models.router import ModelRouter
from app.orchestrator import Orchestrator
from app.orchestrator.agent import Agent, AgentState
from app.orchestrator.events import (
    CallbackEventSink,
    EventStage,
    EventStatus,
    InMemoryEventSink,
    ProgressEvent,
    ProgressEventEmitter,
    sanitize_metadata,
    sanitize_value,
)
from app.orchestrator.execution import Executor, ToolAction
from app.orchestrator.planning import Planner
from app.orchestrator.routing import TaskClassifier, TaskProfile
from app.tools.base import BaseTool
from app.tools.registry import ToolRegistry


class DummyEchoTool(BaseTool):
    @property
    def name(self) -> str:
        return "dummy_echo"

    @property
    def description(self) -> str:
        return "Echoes the input text"

    @property
    def parameters(self) -> dict:
        return {
            "text": {"type": "string", "description": "Text to echo", "required": True}
        }

    def execute(self, text: str) -> str:
        return f"Echoed: {text}"


class DummyFailingTool(BaseTool):
    @property
    def name(self) -> str:
        return "dummy_fail"

    @property
    def description(self) -> str:
        return "Always fails"

    @property
    def parameters(self) -> dict:
        return {}

    def execute(self) -> str:
        return "Error: Internal tool calculation failure."


class TestProgressEventSystem(unittest.TestCase):
    """
    Comprehensive test suite for SOAR Backend Progress and Event System.
    Validates event models, emitter/sink abstraction, real execution checkpoints,
    security/sanitization, and agent loop lifecycle integration.
    """

    def test_progress_event_model_and_serialization(self):
        event = ProgressEvent(
            stage=EventStage.CLASSIFYING,
            status=EventStatus.STARTED,
            message="Classifying task",
            metadata={"source": "test", "task_type": "general"},
            run_id="run-123",
        )

        self.assertIsNotNone(event.event_id)
        self.assertEqual(event.stage, "CLASSIFYING")
        self.assertEqual(event.status, "STARTED")
        self.assertEqual(event.message, "Classifying task")
        self.assertEqual(event.run_id, "run-123")
        self.assertIn("timestamp", event.to_dict())

        d = event.to_dict()
        self.assertEqual(d["event_id"], event.event_id)
        self.assertEqual(d["stage"], "CLASSIFYING")
        self.assertEqual(d["status"], "STARTED")
        self.assertEqual(d["metadata"]["task_type"], "general")

    def test_in_memory_event_sink(self):
        sink = InMemoryEventSink()
        self.assertEqual(len(sink), 0)

        ev1 = ProgressEvent(stage=EventStage.CLASSIFYING, status=EventStatus.STARTED, message="Start")
        ev2 = ProgressEvent(stage=EventStage.CLASSIFYING, status=EventStatus.COMPLETED, message="Done")

        sink.handle_event(ev1)
        sink.handle_event(ev2)

        self.assertEqual(len(sink), 2)
        events = sink.get_events()
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].message, "Start")
        self.assertEqual(events[1].message, "Done")

        dicts = sink.get_event_dicts()
        self.assertEqual(len(dicts), 2)
        self.assertEqual(dicts[0]["message"], "Start")

        sink.clear()
        self.assertEqual(len(sink), 0)

    def test_callback_event_sink(self):
        received = []

        def on_event(ev: ProgressEvent):
            received.append(ev)

        sink = CallbackEventSink(on_event)
        ev = ProgressEvent(stage=EventStage.PLANNING, status=EventStatus.STARTED, message="Planning")
        sink.handle_event(ev)

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].stage, "PLANNING")
        self.assertEqual(received[0].message, "Planning")

    def test_emitter_multiple_sinks(self):
        in_memory = InMemoryEventSink()
        received_callback = []

        emitter = ProgressEventEmitter(sinks=[in_memory])
        emitter.subscribe(lambda ev: received_callback.append(ev))

        emitted = emitter.emit(
            stage=EventStage.TOOL_EXECUTING,
            status=EventStatus.STARTED,
            message="Executing dummy",
            metadata={"tool": "dummy"},
        )

        self.assertEqual(len(in_memory), 1)
        self.assertEqual(len(received_callback), 1)
        self.assertEqual(emitted.stage, "TOOL_EXECUTING")
        self.assertEqual(in_memory.get_events()[0].event_id, emitted.event_id)
        self.assertEqual(received_callback[0].event_id, emitted.event_id)

    def test_metadata_sanitization_privacy_rules(self):
        raw_meta = {
            "task_type": "coding",
            "password": "super_secret_password_123",
            "raw_prompt": "Sensitive internal prompt that should not be in progress events",
            "chain_of_thought": "<think>private model thoughts</think>",
            "result": "Clean output <think>hidden model internal reasoning</think> Done.",
            "huge_output": "x" * 1000,
        }

        sanitized = sanitize_metadata(raw_meta)

        # Excluded sensitive keys
        self.assertNotIn("raw_prompt", sanitized)
        self.assertNotIn("chain_of_thought", sanitized)

        # Redacted secret value
        self.assertIn("password", sanitized)
        self.assertIn("[REDACTED]", sanitized["password"])

        # Stripped think tags
        self.assertNotIn("<think>", sanitized["result"])
        self.assertIn("[thought stripped]", sanitized["result"])

        # Truncated large output
        self.assertTrue(sanitized["huge_output"].endswith("[truncated]"))
        self.assertLess(len(sanitized["huge_output"]), 400)

    def test_orchestrator_direct_answer_emits_full_event_sequence(self):
        registry = ModelRegistry()
        mock_model = MockModel(
            model_id="qwen3:1.7b",
            capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
            fixed_response="Paris is the capital of France.",
        )
        registry.register(mock_model)
        manager = ModelManager(model_registry=registry, default_model_name="qwen3:1.7b")

        emitter = ProgressEventEmitter()
        orchestrator = Orchestrator(model_manager=manager, emitter=emitter)

        res = orchestrator.process_task("What is the capital of France?")

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["execution_mode"], "direct_answer")

        events = res["events"]
        self.assertGreaterEqual(len(events), 4)

        stages = [e["stage"] for e in events]
        self.assertIn("CLASSIFYING", stages)
        self.assertIn("MODEL_SELECTING", stages)
        self.assertIn("GENERATING_OUTPUT", stages)
        self.assertIn("COMPLETED", stages)

        # Verify classification metadata
        classify_ev = next(e for e in events if e["stage"] == "CLASSIFYING" and e["status"] == "COMPLETED")
        self.assertEqual(classify_ev["metadata"]["task_type"], "general")
        self.assertEqual(classify_ev["metadata"]["execution_mode"], "direct_answer")

        # Verify completion event
        complete_ev = next(e for e in events if e["stage"] == "COMPLETED")
        self.assertEqual(complete_ev["status"], "COMPLETED")
        self.assertEqual(complete_ev["message"], "Task completed")

    def test_orchestrator_coding_emits_events(self):
        registry = ModelRegistry()
        mock_coder = MockModel(
            model_id="qwen2.5-coder:1.5b",
            capabilities={ModelCapability.CODING},
            fixed_response="```python\ndef add(a, b):\n    return a + b\n```",
        )
        registry.register(mock_coder)
        manager = ModelManager(model_registry=registry, default_model_name="qwen2.5-coder:1.5b")

        emitter = ProgressEventEmitter()
        orchestrator = Orchestrator(model_manager=manager, emitter=emitter)

        res = orchestrator.process_task("Write a Python function to add two numbers.")

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["execution_mode"], "code")

        events = res["events"]
        stages = [e["stage"] for e in events]
        self.assertIn("CLASSIFYING", stages)
        self.assertIn("MODEL_SELECTING", stages)
        self.assertIn("GENERATING_OUTPUT", stages)
        self.assertIn("COMPLETED", stages)

    def test_orchestrator_coding_with_sandbox_emits_tool_events(self):
        registry = ModelRegistry()
        mock_coder = MockModel(
            model_id="qwen2.5-coder:1.5b",
            capabilities={ModelCapability.CODING},
            fixed_response="```python\nprint(1 + 2)\n```",
        )
        registry.register(mock_coder)
        manager = ModelManager(model_registry=registry, default_model_name="qwen2.5-coder:1.5b")

        emitter = ProgressEventEmitter()
        orchestrator = Orchestrator(model_manager=manager, emitter=emitter)

        res = orchestrator.process_task("Write and test a Python function to sum numbers.")

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["execution_mode"], "code")

        events = res["events"]
        tool_events = [e for e in events if e["stage"] == "TOOL_EXECUTING"]
        self.assertGreaterEqual(len(tool_events), 2)  # STARTED and COMPLETED
        self.assertEqual(tool_events[0]["metadata"]["tool"], "python_sandbox")

    def test_multi_step_agent_emits_planning_tool_and_observing_events(self):
        tool_reg = ToolRegistry()
        tool_reg.register(DummyEchoTool())

        model_reg = ModelRegistry()
        # Planner outputs a plan on iteration 1, then completes on iteration 2
        mock_planner = MockModel(
            model_id="qwen3:1.7b",
            capabilities={ModelCapability.REASONING, ModelCapability.GENERAL},
            fixed_response='{"status": "continue", "thought": "Echo the greeting", "steps": [{"tool": "dummy_echo", "arguments": {"text": "Hello World"}}]}',
        )
        model_reg.register(mock_planner)
        manager = ModelManager(model_registry=model_reg, default_model_name="qwen3:1.7b")

        emitter = ProgressEventEmitter()
        planner = Planner(model_manager=manager, tool_registry=tool_reg, emitter=emitter)
        executor = Executor(tool_registry=tool_reg, emitter=emitter)
        agent = Agent(planner=planner, executor=executor, max_iterations=2, emitter=emitter)

        # Mock the second call to return complete
        def generate_side_effect(prompt, **kwargs):
            if "PREVIOUS OBSERVATIONS" in prompt:
                return '{"status": "complete", "thought": "Done", "steps": []}'
            return '{"status": "continue", "thought": "Echo the greeting", "steps": [{"tool": "dummy_echo", "arguments": {"text": "Hello World"}}]}'

        mock_planner.generate = MagicMock(side_effect=generate_side_effect)

        state = agent.run("Please echo Hello World")

        self.assertEqual(state.status, "completed")
        events = emitter.get_events()
        stages = [e.stage for e in events]

        self.assertIn("PLANNING", stages)
        self.assertIn("TOOL_EXECUTING", stages)
        self.assertIn("OBSERVING", stages)
        self.assertIn("REASONING", stages)
        self.assertIn("COMPLETED", stages)

        # Check tool execution event
        tool_start = next(e for e in events if e.stage == "TOOL_EXECUTING" and e.status == "STARTED")
        self.assertEqual(tool_start.metadata["tool"], "dummy_echo")
        self.assertEqual(tool_start.metadata["arguments"]["text"], "Hello World")

        # Check observation event
        obs_ev = next(e for e in events if e.stage == "OBSERVING")
        self.assertTrue(obs_ev.metadata["success"])
        self.assertIn("Echoed: Hello World", obs_ev.metadata["result_summary"])

        # Check reasoning event in iteration 2
        reason_ev = next(e for e in events if e.stage == "REASONING")
        self.assertEqual(reason_ev.metadata["iteration"], 2)

    def test_tool_failure_emits_failed_event(self):
        tool_reg = ToolRegistry()
        tool_reg.register(DummyFailingTool())

        emitter = ProgressEventEmitter()
        executor = Executor(tool_registry=tool_reg, emitter=emitter)

        action = ToolAction(tool="dummy_fail", arguments={})
        res = executor.execute_action(action, run_id="test-run")

        self.assertEqual(res["status"], "error")
        events = emitter.get_events()
        fail_ev = next(e for e in events if e.stage == "TOOL_EXECUTING" and e.status == "FAILED")
        self.assertEqual(fail_ev.metadata["tool"], "dummy_fail")
        self.assertIn("Internal tool calculation failure", fail_ev.metadata["error"])

    def test_planner_error_emits_failed_event(self):
        model_reg = ModelRegistry()
        mock_planner = MockModel(
            model_id="qwen3:1.7b",
            capabilities={ModelCapability.REASONING, ModelCapability.GENERAL},
            fixed_response="INVALID JSON RESPONSE FROM MODEL",
        )
        model_reg.register(mock_planner)
        manager = ModelManager(model_registry=model_reg, default_model_name="qwen3:1.7b")

        emitter = ProgressEventEmitter()
        planner = Planner(model_manager=manager, emitter=emitter)

        state = AgentState(task="Invalid task test")
        out_state = planner.create_plan(state)

        self.assertEqual(out_state.status, "error")
        events = emitter.get_events()
        fail_ev = next(e for e in events if e.stage == "PLANNING" and e.status == "FAILED")
        self.assertIn("error", fail_ev.metadata)

    def test_model_runtime_fallback_emits_fallback_event(self):
        model_reg = ModelRegistry()
        failing_hard_model = MockModel(
            model_id="qwen2:4b",
            capabilities={ModelCapability.REASONING},
            priority=20,
        )
        # Simulate timeout on 4B model
        failing_hard_model.generate = MagicMock(side_effect=TimeoutError("Inference timed out after 15s"))

        fallback_general_model = MockModel(
            model_id="qwen3:1.7b",
            capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
            priority=10,
            fixed_response="Fallback general model answer.",
        )

        model_reg.register(failing_hard_model)
        model_reg.register(fallback_general_model)

        manager = ModelManager(model_registry=model_reg, default_model_name="qwen3:1.7b")
        emitter = ProgressEventEmitter()

        profile = TaskProfile(
            task_type="reasoning",
            complexity="hard",
            execution_mode="direct_answer",
            original_task="Explain complex root cause",
        )

        res = manager.generate_with_routing(
            "Explain complex root cause",
            profile=profile,
            emitter=emitter,
            run_id="run-fb",
        )

        self.assertTrue(res.fallback_used)
        self.assertEqual(res.actual_model_id, "qwen3:1.7b")

        events = emitter.get_events()
        fb_ev = next(e for e in events if e.stage == "MODEL_SELECTING" and e.status == "IN_PROGRESS")
        self.assertIn("falling back", fb_ev.message)
        self.assertEqual(fb_ev.metadata["fallback_model"], "qwen3:1.7b")


if __name__ == "__main__":
    unittest.main()
