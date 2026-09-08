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
        name = kwargs.get("name", "SOAR")
        return f"Hello from {name}!"


print("[TEST] Initializing ToolRegistry...")
registry = ToolRegistry()

print("\n1. Registering tool...")
hello_tool = HelloTool()
registry.register(hello_tool)
print("Tool registered successfully.")

print("\n2. Retrieving tool by name ('hello')...")
tool = registry.get("hello")
print(f"Retrieved tool: {tool.name}")

print("\n3. Executing tool...")
result = tool.execute(name="SOAR")
print(f"Output: {result}")

print("\n4. Listing registered tools:")
for t in registry.list_tools():
    print(f"- {t.name}: {t.description}")

print("\n5. Testing duplicate registration handling...")
try:
    registry.register(hello_tool)
except ValueError as e:
    print(f"Caught expected ValueError: {e}")

print("\n6. Testing unknown tool handling...")
try:
    registry.get("unknown_tool")
except KeyError as e:
    print(f"Caught expected KeyError: {e}")

print("\n[TEST] All tool registry tests completed successfully!")