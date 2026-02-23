"""File Writer tool — allows the Engineer agent to write test files to disk."""

import json
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import Field


class FileWriterTool(BaseTool):
    """Writes content to a file on disk.

    Used by the Engineer agent to create test files, conftest.py,
    requirements.txt, and other project artifacts.
    """

    name: str = "file_writer"
    description: str = (
        "Writes content to a file. Input should be a JSON string with: "
        "'path' (relative file path, e.g. 'tests/test_pets.py'), "
        "'content' (the file content to write). "
        "Directories will be created automatically."
    )
    output_dir: str = Field(default="./output", description="Base output directory")

    def _run(self, request_json: str) -> str:
        """Write content to a file.

        Args:
            request_json: JSON with 'path' and 'content' keys.

        Returns:
            Confirmation message with the file path.
        """
        try:
            request = json.loads(request_json) if isinstance(request_json, str) else request_json
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON input — {e}"

        file_path = request.get("path", "")
        content = request.get("content", "")

        if not file_path:
            return "Error: 'path' is required."
        if not content:
            return "Error: 'content' is required."

        # Security: prevent path traversal
        if ".." in file_path:
            return "Error: Path traversal ('..') is not allowed."

        try:
            full_path = Path(self.output_dir) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")
            return f"Successfully wrote {len(content)} chars to {full_path}"
        except OSError as e:
            return f"Error writing file: {e}"
