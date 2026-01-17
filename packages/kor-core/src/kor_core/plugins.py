import subprocess
import json
import asyncio
from typing import List, Dict, Any, Optional

class UVManager:
    """
    Wraps module execution using 'uv run'.
    This ensures plugins run in their own ephemeral environments.
    """
    
    @staticmethod
    async def run_plugin(package_name: str, module_path: str, args: List[str] = []) -> str:
        """
        Runs a plugin command using 'uv run --package <pkg> python -m <module>'.
        Returns stdout.
        """
        cmd = [
            "uv", "run",
            "--package", package_name,
            "python", "-m", module_path
        ] + args

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            raise RuntimeError(f"Plugin {package_name} failed: {error_msg}")

        return stdout.decode().strip()

    @staticmethod
    async def list_plugins(plugins_dir: str = "plugins") -> List[str]:
        """
        Scans the plugins directory for subdirectories containing pyproject.toml.
        Returns a list of package names (folder names).
        """
        import os
        from pathlib import Path

        # Assuming plugins_dir is relative to the workspace root or provided absolutely
        # For this implementation, we try to find the workspace root relative to this file
        # This file is in packages/kor-core/src/kor_core/plugins.py
        # Workspace root is likely ../../../../..
        
        # However, usually the app runs from the root in this setup.
        # We will check if 'plugins' exists in CWD first.
        
        path = Path(plugins_dir)
        if not path.exists():
            # If not found, try to look up generic locations or return empty for safety
            return []

        plugins = []
        for entry in os.scandir(path):
            if entry.is_dir() and (Path(entry.path) / "pyproject.toml").exists():
                plugins.append(entry.name)
        
        return plugins
