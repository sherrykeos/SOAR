import os
import tempfile
from pathlib import Path

from app.tools.read_file import ReadFileTool
from app.tools.registry import ToolRegistry


print("[TEST] Starting ReadFileTool tests...", flush=True)

# 1. Create a temporary text file
with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".txt") as temp_file:
    temp_path = temp_file.name
    temp_file.write("SOAR Inspection Report v1.0\nStatus: Approved")

print(f"1. Created temporary test file at: {temp_path}")

try:
    # 2. Register ReadFileTool with ToolRegistry
    print("2. Registering ReadFileTool with ToolRegistry...")
    registry = ToolRegistry()
    registry.register(ReadFileTool())

    # 3. Retrieve tool using 'read_file'
    print("3. Retrieving tool by name 'read_file'...")
    tool = registry.get("read_file")

    # 4. Execute tool against the temporary file
    print("4. Executing read_file tool...")
    contents = tool.execute(file_path=temp_path)

    # 5. Verify the returned contents
    print(f"5. Verifying contents:\n--- BEGIN ---\n{contents}\n--- END ---")
    assert contents == "SOAR Inspection Report v1.0\nStatus: Approved", "Content mismatch!"
    print("Contents verified successfully.")

    # 6. Test a missing file path
    print("\n6. Testing missing file handling...")
    missing_path = "non_existent_file_soar_12345.txt"
    missing_result = tool.execute(file_path=missing_path)
    print(f"Result: {missing_result}")
    assert "File not found" in missing_result, "Missing file handling failed!"

    # 7. Test a directory path
    print("\n7. Testing directory path handling...")
    dir_path = str(Path(temp_path).parent)
    dir_result = tool.execute(file_path=dir_path)
    print(f"Result: {dir_result}")
    assert "is a directory" in dir_result, "Directory path handling failed!"

finally:
    # 8. Clean up the temporary file
    if os.path.exists(temp_path):
        os.remove(temp_path)
        print(f"\n8. Cleaned up temporary test file at: {temp_path}")

print("\n[TEST] All ReadFileTool tests completed successfully!")
