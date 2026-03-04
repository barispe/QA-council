"""Test Runner tool — runs pytest and captures results."""

import json
import subprocess
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import Field


class TestRunnerTool(BaseTool):
    """Runs pytest on test files and returns results.

    Used by the Engineer agent to execute generated tests
    and capture pass/fail information.
    """

    name: str = "test_runner"
    description: str = (
        "Runs pytest on a test directory or file. Input should be a JSON string with: "
        "'path' (path to test file or directory, e.g. 'tests/' or 'tests/test_pets.py'), "
        "optional 'args' (list of extra pytest arguments like ['-v', '--tb=short'])."
    )
    output_dir: str = Field(default="./output", description="Base output directory")
    timeout: int = Field(default=120, description="Max seconds for test run")

    def _run(self, request_json: str) -> str:
        """Run pytest and return results.

        Args:
            request_json: JSON with 'path' and optional 'args'.

        Returns:
            Pytest output with pass/fail summary.
        """
        try:
            request = json.loads(request_json) if isinstance(request_json, str) else request_json
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON input — {e}"

        test_path = request.get("path", "tests/")
        extra_args = request.get("args", ["-v", "--tb=short"])

        full_path = Path(self.output_dir) / test_path

        if not full_path.exists():
            return f"Error: Test path does not exist: {full_path}"

        cmd = ["python", "-m", "pytest", str(full_path)] + extra_args

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(Path(self.output_dir)),
            )

            output = result.stdout
            if result.stderr:
                output += f"\n\nSTDERR:\n{result.stderr}"

            # Truncate if too long
            if len(output) > 4000:
                output = (
                    output[:4000]
                    + f"\n\n... [TRUNCATED — full output is {len(result.stdout)} chars]"
                )

            return (
                f"Exit code: {result.returncode} "
                f"({'PASSED' if result.returncode == 0 else 'FAILED'})\n\n"
                f"{output}"
            )

        except subprocess.TimeoutExpired:
            return f"Error: Test run timed out after {self.timeout}s"
        except FileNotFoundError:
            return "Error: pytest not found. Make sure it's installed."
