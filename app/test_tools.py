from app.tools.base import BaseTool
from app.tools.registry import ToolRegistry


class HelloTool(BaseTool):

    @property
    def name(self) -> str:
        return "hello"

    @property
    def description(self) -> str:
        return "Returns a hello message."

    def execute(self, **kwargs):
        return "Hello from SOAR!"


registry = ToolRegistry()

registry.register(HelloTool())

tool = registry.get("hello")

print(tool.execute())

print("\nRegistered tools:")

for tool in registry.list_tools():
    print(f"- {tool.name}: {tool.description}")