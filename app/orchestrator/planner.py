from app.models.manager import ModelManager
from .state import AgentState


class Planner:

    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager

    def create_plan(self, state: AgentState) -> AgentState:

        prompt = f"""
You are the planning component of SOAR, a sovereign
on-premise AI agent.

Create a simple step-by-step plan for the following task:

TASK:
{state.task}

Rules:
- Return only the numbered steps.
- Each step must describe one concrete action.
- Keep the plan between 2 and 6 steps.
- Do not execute the task.
"""

        print("\n===== SENDING TO MODEL =====")
        print(prompt)
        print("============================\n")

        response = self.model_manager.generate(prompt)

        print("\n===== PLANNER RESPONSE =====")
        print(response)
        print("============================\n")

        state.plan = self._parse_plan(response)

        return state

    def _parse_plan(self, response: str) -> list[str]:
        steps = []

        for line in response.splitlines():
            line = line.strip()

            if not line:
                continue

            # Remove common numbering formats:
            # 1. Step
            # 1) Step
            if line[0].isdigit():

                parts = line.split(".", 1)

                if len(parts) == 2:
                    line = parts[1].strip()

                else:
                    parts = line.split(")", 1)

                    if len(parts) == 2:
                        line = parts[1].strip()

            if line:
                steps.append(line)

        return steps