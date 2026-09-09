from app.tools.base import BaseTool
from app.tools.docx_creator import DOCXCreatorTool
from app.tools.pdf_creator import PDFCreatorTool
from app.tools.pdf_reader import PDFReaderTool
from app.tools.python_sandbox import PythonSandboxTool
from app.tools.read_file import ReadFileTool
from app.tools.registry import ToolRegistry


class HelloTool(BaseTool):

    @property
    def name(self) -> str:
        return "hello"

    @property
    def description(self) -> str:
        return "Returns a hello message."

    @property
    def parameters(self) -> dict:
        return {
            "name": {
                "type": "string",
                "description": "Name of the entity to greet.",
                "required": True,
            }
        }

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
assert tool.name == "hello"
print(f"Retrieved tool: {tool.name}")

print("\n3. Executing tool...")
result = tool.execute(name="SOAR")
assert result == "Hello from SOAR!"
print(f"Output: {result}")

print("\n4. Testing tool schema exposure across all tools...")
all_tools = [
    hello_tool,
    ReadFileTool(),
    PDFReaderTool(),
    DOCXCreatorTool(),
    PDFCreatorTool(),
    PythonSandboxTool(),
]
for t in all_tools:
    assert isinstance(t.parameters, dict), f"Tool {t.name} parameters must be a dict"
    assert len(t.parameters) > 0, f"Tool {t.name} parameters must not be empty"
    print(f"- {t.name} schema: {list(t.parameters.keys())}")

print("\n5. Testing argument validation on HelloTool...")
# Valid arguments
assert hello_tool.validate_arguments({"name": "SOAR"}) is None

# Missing required argument
missing_err = hello_tool.validate_arguments({})
assert missing_err is not None
assert "Missing required parameter 'name'" in missing_err
print(f"Missing argument correctly caught: {missing_err}")

# Invalid placeholder 'parameter_name'
placeholder_err = hello_tool.validate_arguments({"parameter_name": "name"})
assert placeholder_err is not None
assert "Invalid placeholder argument 'parameter_name'" in placeholder_err
print(f"Placeholder argument correctly rejected: {placeholder_err}")

print("\n6. Testing duplicate registration handling...")
try:
    registry.register(hello_tool)
except ValueError as e:
    print(f"Caught expected ValueError: {e}")

print("\n7. Testing unknown tool handling...")
try:
    registry.get("unknown_tool")
except KeyError as e:
    print(f"Caught expected KeyError: {e}")

print("\n[TEST] All tool registry tests completed successfully!")