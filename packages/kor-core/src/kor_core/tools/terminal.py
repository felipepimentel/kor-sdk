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
    use_sandbox: bool = False
    sandbox_image: str = "python:3.12-slim"
    
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
        
        # 3. Apply Sandboxing if enabled
        final_command = command
        if self.use_sandbox:
            import os
            cwd = os.getcwd()
            # Construct Docker command
            # -rm: Remove container after exit
            # -v: Mount current directory to /workspace
            # -w: Set working directory to /workspace
            # --network none: Disable network by default for safety (can be configurable later)
            # user: Run as current user to avoid permission issues on files? 
            #       (Often tricky in Docker, defaulting to root inside container for now 
            #       but mapping files might be issue. Kept simple for V1)
            
            # Simple sanitization for strict shell usage
            safe_cmd = shlex.quote(command)
            
            final_command = (
                f"docker run --rm -v {cwd}:/workspace -w /workspace "
                f"{self.sandbox_image} /bin/sh -c {safe_cmd}"
            )

        try:
            result = subprocess.run(
                final_command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=60
            )
            return result.stdout or result.stderr
        except Exception as e:
            return f"Error executing command: {e}"
