import os
from pathlib import Path
from typing import Any

from .base import BaseTool


class ReadFileTool(BaseTool):

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Reads the contents of a local text file using UTF-8 encoding."

    @property
    def parameters(self) -> dict[str, dict[str, Any]]:
        return {
            "file_path": {
                "type": "string",
                "description": "Path to the local text file to read.",
                "required": True,
            }
        }

    def execute(self, **kwargs) -> str:
        file_path = kwargs.get("file_path") or kwargs.get("path")

        if not file_path:
            return "Error: Missing required parameter 'file_path' (or 'path')."

        target_path = Path(file_path)

        # Fallback to common directories if relative file not found directly in cwd
        if not target_path.exists():
            if (Path("inputs") / file_path).exists():
                target_path = Path("inputs") / file_path
            elif (Path("sandbox/workspace") / file_path).exists():
                target_path = Path("sandbox/workspace") / file_path
            else:
                return f"Error: File not found at '{file_path}'."

        if target_path.is_dir():
            return f"Error: Path '{file_path}' is a directory, not a file."

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            return f"Error: Unable to decode file '{file_path}' as UTF-8 text."
        except PermissionError:
            return f"Error: Permission denied when reading '{file_path}'."
        except Exception as e:
            return f"Error reading file '{file_path}': {str(e)}"
