"""Script execution utilities."""

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
import shlex
import logging

from ..exceptions import ScriptExecutionError

logger = logging.getLogger(__name__)


class ScriptRunner:
    """Execute shell scripts with proper error handling."""

    def __init__(self, scripts_dir: Path, timeout: int = 30):
        self.scripts_dir = scripts_dir
        self.timeout = timeout

    async def run_script(
        self,
        script_name: str,
        args: Optional[List[str]] = None,
        json_output: bool = False,
        cwd: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Execute a shell script and return output."""
        script_path = self.scripts_dir / script_name

        if not script_path.exists():
            raise ScriptExecutionError(
                f"Script not found: {script_name}",
                details={"script_path": str(script_path)},
                suggestions=["Check that spec-kit scripts are properly installed"]
            )

        # Build command
        cmd = [str(script_path)]
        if json_output:
            cmd.append("--json")
        if args:
            cmd.extend(args)

        logger.info(f"Executing script: {' '.join(cmd)}")

        # Execute script
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd or self.scripts_dir.parent
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )

            if process.returncode != 0:
                error_output = stderr.decode() if stderr else stdout.decode()
                raise ScriptExecutionError(
                    f"Script {script_name} failed with exit code {process.returncode}",
                    details={
                        "stdout": stdout.decode() if stdout else "",
                        "stderr": stderr.decode() if stderr else "",
                        "exit_code": process.returncode
                    },
                    suggestions=["Check script output for details"]
                )

            output = stdout.decode().strip()

            if json_output:
                try:
                    return json.loads(output)
                except json.JSONDecodeError as e:
                    # Try to parse as key-value pairs (fallback for non-JSON scripts)
                    return self._parse_key_value_output(output)

            return {"output": output}

        except asyncio.TimeoutError:
            raise ScriptExecutionError(
                f"Script {script_name} timed out after {self.timeout} seconds",
                suggestions=["Increase timeout", "Check if script is hanging"]
            )
        except Exception as e:
            if isinstance(e, ScriptExecutionError):
                raise
            raise ScriptExecutionError(
                f"Failed to execute script {script_name}",
                details={"error": str(e)},
                suggestions=["Check script permissions", "Ensure script is executable"]
            )

    def _parse_key_value_output(self, output: str) -> Dict[str, str]:
        """Parse key-value output from scripts."""
        result = {}
        for line in output.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                result[key.strip()] = value.strip()
        return result

    async def check_script_exists(self, script_name: str) -> bool:
        """Check if a script exists."""
        script_path = self.scripts_dir / script_name
        return script_path.exists() and script_path.is_file()