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
    
    # Callback for confirmation (set by CLI)
    confirmation_callback: Optional[Callable[[str], bool]] = None

    def _run(self, command: str) -> str:
        # 1. Use tool-specific callback if set
        if self.confirmation_callback:
            if not self.confirmation_callback(command):
                return "[Cancelled by user]"
        
        # 2. Otherwise use the Kernel's global permission system
        elif self.requires_confirmation:
            from ..kernel import get_kernel
            k = get_kernel()
            if not k.request_permission("terminal_command", command):
                return "[Permission Denied]"
        
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=60
            )
            return result.stdout or result.stderr
        except Exception as e:
            return f"Error executing command: {e}"
