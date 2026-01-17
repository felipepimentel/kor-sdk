from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class PluginPermission(BaseModel):
    scope: str
    reason: str

class PluginManifest(BaseModel):
    """
    Schema for plugin.json
    Inspired by Claude Code's manifest.
    """
    name: str = Field(pattern=r"^[a-z0-9-]+$")
    version: str
    description: str
    permissions: List[PluginPermission] = Field(default_factory=list)
    entry_point: Optional[str] = None # For python module loading
    
    # Sub-capabilities paths (relative to plugin root)
    commands_dir: str = "commands"
    agents_dir: str = "agents"
    skills_dir: str = "skills"
