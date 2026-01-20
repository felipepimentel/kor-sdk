"""
Sandbox System Implementation
"""
import abc
from pathlib import Path
from typing import Optional, List
import subprocess
import shlex
import logging

logger = logging.getLogger(__name__)

class SandboxProtocol(abc.ABC):
    """
    Protocol for agent execution environments.
    """
    @abc.abstractmethod
    async def start(self):
        """Initialize the sandbox resource."""
        pass

    @abc.abstractmethod
    async def stop(self):
        """Cleanup the sandbox resource."""
        pass
        
    @abc.abstractmethod
    async def run_command(self, command: str, cwd: Optional[str] = None) -> str:
        """Run a shell command."""
        pass
        
    @abc.abstractmethod
    async def read_file(self, path: str) -> str:
        """Read a file."""
        pass
        
    @abc.abstractmethod
    async def write_file(self, path: str, content: str) -> str:
        """Write to a file."""
        pass
        
    @abc.abstractmethod
    async def list_dir(self, path: str) -> List[str]:
        """List directory contents."""
        pass

class LocalSandbox(SandboxProtocol):
    """
    Executes commands directly on the host machine.
    """
    async def start(self):
        pass # No-op for local

    async def stop(self):
        pass # No-op for local

    async def run_command(self, command: str, cwd: Optional[str] = None) -> str:
        import asyncio
        try:
            # Run in thread pool to avoid blocking the main event loop
            # because subprocess.run is blocking.
            # In DockerSandbox, this will be a real async call.
            def _sync_run():
                return subprocess.run(
                    command,
                    cwd=cwd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
            
            result = await asyncio.to_thread(_sync_run)
            return result.stdout or result.stderr
        except Exception as e:
            return f"Error executing command: {e}"

    async def read_file(self, path: str) -> str:
        import asyncio
        p = Path(path).expanduser()
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return await asyncio.to_thread(p.read_text)

    async def write_file(self, path: str, content: str) -> str:
        import asyncio
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(p.write_text, content)
        return f"Successfully wrote {len(content)} bytes."

    async def list_dir(self, path: str) -> List[str]:
        import asyncio
        p = Path(path).expanduser()
        if not p.exists():
             raise FileNotFoundError(f"Directory not found: {path}")
             
        def _get_items():
            return [f"{'[DIR] ' if i.is_dir() else '[FILE] '}{i.name}" for i in p.iterdir()]
            
        return await asyncio.to_thread(_get_items)

class InMemorySandbox(SandboxProtocol):
    """
    Simulates a filesystem and shell in memory.
    Perfect for unit tests and safe evaluations.
    """
    def __init__(self, initial_files: Optional[dict[str, str]] = None):
        self.files = initial_files or {}
        self.cwd = "/"

    async def start(self):
        pass

    async def stop(self):
        self.files.clear()

    async def run_command(self, command: str, cwd: Optional[str] = None) -> str:
        # Very basic shell simulation
        cmd_parts = command.split()
        if not cmd_parts:
            return ""
        
        prog = cmd_parts[0]
        if prog == "ls":
            return "\n".join(self.files.keys())
        elif prog == "echo":
            return " ".join(cmd_parts[1:])
        elif prog == "cat":
            if len(cmd_parts) > 1:
                return await self.read_file(cmd_parts[1])
            return ""
        elif prog == "pwd":
            return self.cwd
        return f"Mock shell: command not found: {prog}"

    async def read_file(self, path: str) -> str:
        if path not in self.files:
            raise FileNotFoundError(f"File not found: {path} (in memory)")
        return self.files[path]

    async def write_file(self, path: str, content: str) -> str:
        self.files[path] = content
        return f"Successfully wrote {len(content)} bytes (in memory)."

    async def list_dir(self, path: str) -> List[str]:
        # Simple flat list simulation
        results = []
        path_str = str(path).strip("/")
        for k in self.files.keys():
            results.append(k)
        return results
