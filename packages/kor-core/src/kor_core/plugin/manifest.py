from typing import List, Optional, Dict, Union
from pydantic import BaseModel, Field, field_validator

class PluginPermission(BaseModel):
    scope: str
    reason: str

class AgentDefinition(BaseModel):
    """Definition of an agent graph provided by a plugin."""
    id: str = Field(pattern=r"^[a-z0-9-]+$")
    name: str
    description: str
    entry: str  # "module.path:function_name" that returns a CompiledGraph

class PluginManifest(BaseModel):
    """
    Schema for plugin.json
    Standardized manifest format for KOR plugins.
    
    Required fields:
        - name: Unique plugin identifier (e.g., 'kor-plugin-my-feature')
        - version: Semantic version (e.g., '0.1.0')
        - description: Human-readable description
        
    Optional fields:
        - entry_point: Python module:Class for plugin initialization
        - provides: List of capabilities this plugin provides
        - dependencies: List of capability names this plugin requires
        - agents: List of agent definitions
    """
    # Core fields
    name: str = Field(pattern=r"^[a-z0-9-]+$", description="Unique plugin identifier")
    version: str = Field(description="Semantic version (x.y.z)")
    description: str = Field(description="Human-readable description")
    
    # Entry point
    entry_point: Optional[str] = Field(
        default=None, 
        description="Python module:Class (e.g., 'my_plugin:MyPlugin')"
    )
    
    # Capabilities
    provides: List[str] = Field(
        default_factory=list,
        description="List of capabilities this plugin provides"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="List of capability names required by this plugin"
    )
    
    # Permissions
    permissions: List[PluginPermission] = Field(default_factory=list)
    
    # Agents provided by this plugin
    agents: List[AgentDefinition] = Field(default_factory=list)
    
    # Sub-capability paths (relative to plugin root)
    commands_dir: str = "commands"
    agents_dir: str = "agents"
    skills_dir: str = "skills"
    
    @field_validator('dependencies', mode='before')
    @classmethod
    def normalize_dependencies(cls, v):
        """Convert dict-style dependencies to list for backward compatibility."""
        if isinstance(v, dict):
            # Convert {"kor-core": ">=0.1.0"} to ["kor-core"]
            return list(v.keys())
        return v
