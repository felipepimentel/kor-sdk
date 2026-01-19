"""
Agent Models - Unified agent definition for KOR SDK.

Provides a single AgentDefinition class that works for:
- Agents defined in plugin.json (entry point Python)
- Declarative agents in markdown/yaml
- Agents defined in config.toml
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class AgentDefinition:
    """
    Unified agent definition for both manifest and declarative agents.
    
    This is the canonical representation of an agent in the KOR system.
    It can be populated from:
    - plugin.json manifests (with Python entry points)
    - Declarative markdown/yaml files (no Python required)
    - config.toml agent definitions
    
    Attributes:
        id: Unique identifier (e.g., 'code-reviewer')
        name: Human-readable name
        description: What the agent does
        entry: Entry point - Python path or None for declarative
        system_prompt: Instructions for the agent
        tools: List of tool names
        skills: List of skill names
        model: Optional model override
        temperature: Optional temperature override
        source_path: Path to definition file (if loaded from disk)
    
    Example:
        ```python
        # From manifest
        agent = AgentDefinition(
            id="security-auditor",
            name="Security Auditor",
            description="Audits code for security issues",
            entry="security_plugin:create_auditor_graph"
        )
        
        # From declarative markdown
        agent = AgentDefinition(
            id="code-reviewer",
            name="Code Reviewer",
            description="Reviews code for quality",
            system_prompt="You are a senior code reviewer...",
            tools=["read_file", "search_symbols"],
            skills=["python-best-practices"]
        )
        ```
    """
    id: str
    name: str
    description: str = ""
    entry: Optional[str] = None  # None = declarative agent
    system_prompt: str = ""
    tools: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    model: Optional[str] = None
    temperature: Optional[float] = None
    source_path: Optional[Path] = None
    
    # Additional fields for compatibility with existing manifest format
    role: str = ""
    goal: str = ""
    llm_purpose: str = "default"
    
    @property
    def is_declarative(self) -> bool:
        """Check if this is a declarative agent (no Python entry point)."""
        return self.entry is None or self.entry.startswith("declarative:")
    
    @property
    def searchable_text(self) -> str:
        """Combined text for search indexing."""
        return f"{self.id} {self.name} {self.description}"


__all__ = ["AgentDefinition"]
