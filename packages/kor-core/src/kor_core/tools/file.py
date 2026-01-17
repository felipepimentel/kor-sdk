"""
File Tools for KOR agents.
"""

from typing import Type
from pathlib import Path
from pydantic import BaseModel, Field
from .base import KorTool

class ReadFileInput(BaseModel):
    path: str = Field(description="Path to the file to read")

class WriteFileInput(BaseModel):
    path: str = Field(description="Path to the file to write")
    content: str = Field(description="Content to write to the file")

class ListDirInput(BaseModel):
    path: str = Field(description="Path to the directory to list", default=".")

class ReadFileTool(KorTool):
    name: str = "read_file"
    description: str = "Reads the content of a file."
    args_schema: Type[BaseModel] = ReadFileInput

    def _run(self, path: str) -> str:
        try:
            file_path = Path(path).expanduser()
            if not file_path.exists():
                return f"Error: File not found: {path}"
            return file_path.read_text()
        except Exception as e:
            return f"Error reading file: {e}"

class WriteFileTool(KorTool):
    name: str = "write_file"
    description: str = "Writes content to a file."
    args_schema: Type[BaseModel] = WriteFileInput
    requires_confirmation: bool = True

    def _run(self, path: str, content: str) -> str:
        try:
            file_path = Path(path).expanduser()
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            return f"Successfully wrote {len(content)} bytes to {path}"
        except Exception as e:
            return f"Error writing file: {e}"

class ListDirTool(KorTool):
    name: str = "list_dir"
    description: str = "Lists contents of a directory."
    args_schema: Type[BaseModel] = ListDirInput

    def _run(self, path: str = ".") -> str:
        try:
            dir_path = Path(path).expanduser()
            if not dir_path.exists():
                return f"Error: Directory not found: {path}"
            items = list(dir_path.iterdir())
            result = []
            for item in sorted(items):
                prefix = "[DIR] " if item.is_dir() else "[FILE]"
                result.append(f"{prefix} {item.name}")
            return "\n".join(result) if result else "(empty directory)"
        except Exception as e:
            return f"Error listing directory: {e}"
