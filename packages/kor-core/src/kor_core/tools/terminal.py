import subprocess
import shlex
from typing import Type, Optional, Callable
from pydantic import BaseModel, Field
from .base import KorTool

class TerminalInput(BaseModel):
    command: str = Field(description="The shell command to execute")

class TerminalTool(KorTool):
    name: str = "terminal"
    description: str = "Executes a command in the shell. Requires user confirmation."
    args_schema: Type[BaseModel] = TerminalInput
    requires_confirmation: bool = True
    
    # Sandbox Configuration
    # Deprecated: usage is now controlled by Kernel.sandbox implementation
    use_sandbox: bool = False 
    sandbox_image: str = "python:3.12-slim" # Kept for backward compat in signature but unused
    
    # Callback for confirmation (set by CLI)
    confirmation_callback: Optional[Callable[[str], bool]] = None

    async def _arun(self, command: str) -> str:
        from ..kernel import get_kernel
        k = get_kernel()

        # 1. Use tool-specific callback if set
        if self.confirmation_callback:
            # We assume the callback might be sync or async
            # For now keeping it simple
            if not self.confirmation_callback(command):
                return "[Cancelled by user]"
        
        # 2. Otherwise use the Kernel's global permission system
        elif self.requires_confirmation:
            if not k.request_permission("terminal_command", command):
                return "[Permission Denied]"
        
        # 3. Delegate to Kernel Sandbox (ASYNC)
        return await k.sandbox.run_command(command)

    def _run(self, command: str) -> str:
        import asyncio
        import logging
        try:
            # Sync wrapper for async tool
            # Warning: can fail if loop is already running, which is common in KOR
            # But BaseTool requires _run implementation or it's not a valid tool
            loop = asyncio.get_event_loop()
            if loop.is_running():
                 # This is the tricky part of sync/async bridging in tools
                 return "[Sync execution not supported in active loop. Use async runner.]"
            return asyncio.run(self._arun(command))
        except Exception as e:
            return f"Error: {e}"
