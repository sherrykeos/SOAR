import json
from typing import Any, Dict, Optional

from ..execution.action import ToolAction
from .state import AgentState


class RecoveryManager:
    """
    Manages failure fingerprinting and recovery strategies in the SOAR Agent loop.
    Prevents the agent from endlessly repeating identical failing tool invocations
    and constructs structured recovery observations.
    """

    @staticmethod
    def fingerprint_arguments(arguments: Dict[str, Any]) -> str:
        """Produces a normalized, deterministic string representation of tool arguments."""
        try:
            return json.dumps(arguments, sort_keys=True)
        except (TypeError, ValueError):
            return str(arguments)

    @classmethod
    def check_repeated_failure(
        cls,
        state: AgentState,
        step: ToolAction,
    ) -> Optional[Dict[str, Any]]:
        """
        Checks whether the tool action matches a previous failure fingerprint in this execution run.
        Returns a structured error result dict if repeated failure is detected, or None otherwise.
        """
        norm_args = cls.fingerprint_arguments(step.arguments)
        prev_failure = next(
            (
                f for f in state.failure_fingerprints
                if f.get("tool") == step.tool and f.get("args") == norm_args
            ),
            None,
        )

        if not prev_failure:
            return None

        prev_err_msg = prev_failure.get("error", "Action previously failed.")
        repeated_obs_msg = (
            f"REPEATED FAILING ACTION DETECTED:\n"
            f"The action '{step.tool}' with arguments {step.arguments} already failed previously in this run with error:\n"
            f"'{prev_err_msg}'\n\n"
            f"DO NOT repeat the exact same failing action. Correct the argument names, fix file paths, or choose another valid approach."
        )

        return {
            "status": "error",
            "tool": step.tool,
            "error": repeated_obs_msg,
            "is_repeated_failure": True,
            "observation_message": repeated_obs_msg,
        }

    @classmethod
    def record_failure(
        cls,
        state: AgentState,
        step: ToolAction,
        error_message: Any,
    ) -> None:
        """Records the failure fingerprint of a failed tool action in state."""
        norm_args = cls.fingerprint_arguments(step.arguments)
        state.failure_fingerprints.append({
            "tool": step.tool,
            "args": norm_args,
            "error": str(error_message)[:300],
        })
