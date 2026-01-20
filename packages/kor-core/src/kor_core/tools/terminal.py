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

    def _run(self, command: str) -> str:
        from ..kernel import get_kernel
        k = get_kernel()

        # 1. Use tool-specific callback if set
        if self.confirmation_callback:
            if not self.confirmation_callback(command):
                return "[Cancelled by user]"
        
        # 2. Otherwise use the Kernel's global permission system
        elif self.requires_confirmation:
            if not k.request_permission("terminal_command", command):
                return "[Permission Denied]"
        
        # 3. Delegate to Kernel Sandbox
        # The sandbox (Local or Docker) handles the actual execution details.
        return k.sandbox.run_command(command)
