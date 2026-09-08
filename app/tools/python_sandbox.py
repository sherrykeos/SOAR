import ast
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional

from .base import BaseTool


class PythonSandboxTool(BaseTool):
    """
    Agent tool for executing Python code locally in an isolated sandbox workspace.
    Restricts execution to the root 'sandbox/workspace/' directory and validates
    code against AST security rules before running.
    """

    def __init__(
        self,
        base_sandbox_dir: str | Path = "sandbox",
        default_timeout: int = 10,
    ):
        self.base_dir = Path(base_sandbox_dir).resolve()
        self.workspace_dir = (self.base_dir / "workspace").resolve()
        self.temp_dir = (self.base_dir / "temp").resolve()
        self.default_timeout = default_timeout

        # Ensure sandbox workspace and temp directories exist automatically
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return "python_sandbox"

    @property
    def description(self) -> str:
        return (
            "Executes Python code locally in an isolated sandbox workspace. "
            "Pass 'code' as a parameter. Files created in the script are stored in the sandbox workspace."
        )

    def _validate_code_security(self, code: str) -> Optional[str]:
        """
        Inspects Python code AST for prohibited security violations:
        - Network libraries (socket, requests, urllib, http.client, etc.)
        - Subprocess / shell execution (subprocess, os.system, etc.)
        - Path traversal escapes (../, ../..)
        Returns an error message if a violation is detected, otherwise None.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return f"Syntax error in code: {e.msg} at line {e.lineno}"

        # Disallowed modules
        disallowed_modules = {
            "socket",
            "urllib",
            "requests",
            "httpx",
            "http",
            "subprocess",
            "webbrowser",
            "ftplib",
            "smtplib",
            "paramiko",
            "importlib",
            "telnetlib",
            "xmlrpc",
        }

        disallowed_functions = {"system", "popen", "spawn", "spawnl", "execv", "execve", "fork"}

        for node in ast.walk(tree):
            # Check imports: import x
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_module = alias.name.split(".")[0]
                    if root_module in disallowed_modules or alias.name in disallowed_modules:
                        return f"Security violation: Network/Subprocess module '{alias.name}' is prohibited in the sandbox."

            # Check imports: from x import y
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_module = node.module.split(".")[0]
                    if root_module in disallowed_modules or node.module in disallowed_modules:
                        return f"Security violation: Network/Subprocess module '{node.module}' is prohibited in the sandbox."

            # Check function calls like __import__ or dangerous os calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id == "__import__":
                        return f"Security violation: Dynamic import '{node.func.id}' is prohibited in the sandbox."
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in disallowed_functions:
                        return f"Security violation: Execution of '{node.func.attr}' is prohibited in the sandbox."

            # Check string literals for directory traversal escape attempts
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                val = node.value
                if ".." in val or "/.." in val or "\\.." in val:
                    return f"Security violation: Path traversal escape sequence '{val}' is prohibited in the sandbox."

        return None

    def execute(self, **kwargs: Any) -> str:
        code = kwargs.get("code")
        if not code or not isinstance(code, str) or not code.strip():
            return "Error: Missing required parameter 'code'."

        timeout_arg = kwargs.get("timeout")
        timeout = int(timeout_arg) if timeout_arg is not None else self.default_timeout

        # 1. Security validation
        violation = self._validate_code_security(code)
        if violation:
            return f"Error: {violation}"

        # 2. Write script to temporary runner file in sandbox temp directory
        script_file = self.temp_dir / f"script_{int(time.time() * 1000)}.py"

        try:
            script_file.write_text(code, encoding="utf-8")

            # Snapshot existing workspace files before execution
            before_files = set(self.workspace_dir.iterdir())

            # 3. Build restricted execution environment
            restricted_env = {
                "PYTHONUNBUFFERED": "1",
                "PATH": os.environ.get("PATH", ""),
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
                "TEMP": str(self.temp_dir),
                "TMP": str(self.temp_dir),
            }

            # 4. Execute in subprocess isolated to workspace_dir
            start_time = time.time()
            proc = subprocess.run(
                [sys.executable, str(script_file)],
                cwd=str(self.workspace_dir),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=restricted_env,
            )
            elapsed_time = round(time.time() - start_time, 3)

            # Snapshot newly created workspace files
            after_files = set(self.workspace_dir.iterdir())
            new_files = [f.name for f in (after_files - before_files)]

            # 5. Format results cleanly
            stdout_content = proc.stdout.strip()
            stderr_content = proc.stderr.strip()

            if proc.returncode == 0:
                output_parts = [f"Status: Success (Execution time: {elapsed_time}s)"]
                if stdout_content:
                    output_parts.append(f"Output:\n{stdout_content}")
                if new_files:
                    output_parts.append(f"Workspace files created: {', '.join(new_files)}")
                if not stdout_content and not new_files:
                    output_parts.append("Output: Code executed with no standard output.")
                return "\n\n".join(output_parts)
            else:
                output_parts = [f"Status: Failed (Exit code {proc.returncode}, {elapsed_time}s)"]
                if stdout_content:
                    output_parts.append(f"Standard Output:\n{stdout_content}")
                if stderr_content:
                    output_parts.append(f"Error:\n{stderr_content}")
                return "\n\n".join(output_parts)

        except subprocess.TimeoutExpired:
            return f"Error: Code execution timed out after {timeout} seconds."
        except Exception as e:
            return f"Error running sandbox execution: {str(e)}"
        finally:
            # Clean up temporary runner script
            if script_file.exists():
                try:
                    script_file.unlink()
                except OSError:
                    pass
