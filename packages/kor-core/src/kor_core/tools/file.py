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

    async def _arun(self, path: str) -> str:
        try:
            from ..kernel import get_kernel
            return await get_kernel().sandbox.read_file(path)
        except Exception as e:
            return f"Error reading file: {e}"

    def _run(self, path: str) -> str:
        return "[Sync execution not supported. Use async runner.]"

class WriteFileTool(KorTool):
    name: str = "write_file"
    description: str = "Writes content to a file."
    args_schema: Type[BaseModel] = WriteFileInput
    requires_confirmation: bool = True

    async def _arun(self, path: str, content: str) -> str:
        try:
            from ..kernel import get_kernel
            return await get_kernel().sandbox.write_file(path, content)
        except Exception as e:
            return f"Error writing file: {e}"

    def _run(self, path: str, content: str) -> str:
        return "[Sync execution not supported. Use async runner.]"

class ListDirTool(KorTool):
    name: str = "list_dir"
    description: str = "Lists contents of a directory."
    args_schema: Type[BaseModel] = ListDirInput

    async def _arun(self, path: str = ".") -> str:
        try:
            from ..kernel import get_kernel
            items = await get_kernel().sandbox.list_dir(path)
            return "\n".join(items) if items else "(empty directory)"
        except Exception as e:
            return f"Error listing directory: {e}"

    def _run(self, path: str = ".") -> str:
        return "[Sync execution not supported. Use async runner.]"
