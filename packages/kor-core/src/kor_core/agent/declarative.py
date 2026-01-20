"""
Declarative Agent System

Provides support for defining agents using Markdown/YAML files instead of Python code.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING
import logging

from ..utils import parse_frontmatter

if TYPE_CHECKING:
    from .registry import AgentRegistry
    from .models import AgentDefinition

logger = logging.getLogger(__name__)


@dataclass
class DeclarativeAgentDefinition:
    """
    Agent definition loaded from a markdown/YAML file.
    
    This is a higher-level abstraction than AgentDefinition from manifest.py,
    designed for fully declarative agent configuration.
    
    Attributes:
        id: Unique identifier for the agent
        name: Human-readable name
        description: What the agent does
        system_prompt: The agent's system prompt/instructions
        skills: List of skill names to load
        tools: List of tool names to make available
        model: Optional model override (uses default if not specified)
        temperature: Optional temperature override
        source_path: Path to the source file
    """
    id: str
    name: str
    description: str
    system_prompt: str = ""
    skills: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    model: Optional[str] = None
    temperature: Optional[float] = None
    source_path: Optional[Path] = None
    
    def to_manifest_definition(self) -> "AgentDefinition":
        """
        Convert to a manifest AgentDefinition for compatibility.
        
        Uses a special 'declarative:' prefix to indicate runtime graph building.
        """
        from .models import AgentDefinition
        return AgentDefinition(
            id=self.id,
            name=self.name,
            description=self.description,
            entry=f"declarative:{self.id}"  # Special marker for declarative agents
        )





class AgentLoader:
    """
    Loads declarative agent definitions from filesystem.
    
    Expected file format (agents/*.md):
    ```markdown
    ---
    id: code-reviewer
    name: Code Reviewer
    description: Reviews code for quality and best practices
    skills: [code-review, python-best-practices]
    tools: [read-file, search-symbols]
    model: gpt-4o
    temperature: 0.3
    ---
    
    ## System Prompt
    
    You are a senior code reviewer. Your task is to analyze code
    for quality, security issues, and best practices.
    
    ## Guidelines
    
    1. Check error handling thoroughly
    2. Look for security vulnerabilities
    3. Suggest performance improvements
    ```
    """
    
    def __init__(self, registry: Optional["AgentRegistry"] = None):
        """
        Initialize the AgentLoader.
        
        Args:
            registry: Optional AgentRegistry to auto-register loaded agents
        """
        self._registry = registry
        self._definitions: Dict[str, DeclarativeAgentDefinition] = {}
    
    def load_directory(self, directory: Path) -> List[DeclarativeAgentDefinition]:
        """
        Load all .md agent definitions from a directory.
        
        Args:
            directory: Path to the agents directory
            
        Returns:
            List of loaded DeclarativeAgentDefinition objects
        """
        loaded = []
        
        if not directory.exists():
            logger.debug(f"Agents directory does not exist: {directory}")
            return loaded
        
        # Look for both .md and .yaml/.yml files
        for pattern in ["*.md", "*.yaml", "*.yml"]:
            for file_path in directory.glob(pattern):
                try:
                    definition = self.load_file(file_path)
                    if definition:
                        self._definitions[definition.id] = definition
                        loaded.append(definition)
                        
                        # Register with AgentRegistry if provided
                        if self._registry:
                            manifest_def = definition.to_manifest_definition()
                            self._registry.register(manifest_def)
                        
                        logger.info(f"Loaded declarative agent: {definition.name} ({definition.id})")
                except Exception as e:
                    logger.error(f"Failed to load agent from {file_path}: {e}")
        
        return loaded
    
    def load_file(self, file_path: Path) -> Optional[DeclarativeAgentDefinition]:
        """
        Load a single agent definition from a file.
        
        Args:
            file_path: Path to the agent definition file
            
        Returns:
            DeclarativeAgentDefinition or None if loading failed
        """
        content = file_path.read_text()
        
        # Handle YAML files differently
        if file_path.suffix in [".yaml", ".yml"]:
            return self._load_yaml_file(file_path, content)
        
        # Parse markdown with frontmatter
        frontmatter, body = parse_frontmatter(content)
        
        # Extract fields from frontmatter
        agent_id = frontmatter.get("id", file_path.stem)
        name = frontmatter.get("name", agent_id.replace("-", " ").title())
        description = frontmatter.get("description", "")
        skills = frontmatter.get("skills", [])
        tools = frontmatter.get("tools", [])
        model = frontmatter.get("model")
        temperature = frontmatter.get("temperature")
        
        # Normalize lists
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",")]
        if isinstance(tools, str):
            tools = [t.strip() for t in tools.split(",")]
        
        # The body becomes the system prompt
        system_prompt = body.strip()
        
        return DeclarativeAgentDefinition(
            id=agent_id,
            name=name,
            description=description,
            system_prompt=system_prompt,
            skills=skills,
            tools=tools,
            model=model,
            temperature=temperature,
            source_path=file_path
        )
    
    def _load_yaml_file(self, file_path: Path, content: str) -> Optional[DeclarativeAgentDefinition]:
        """Load agent definition from a YAML file."""
        try:
            import yaml
            data = yaml.safe_load(content)
        except ImportError:
            logger.error("PyYAML required for YAML agent definitions")
            return None
        except Exception as e:
            logger.error(f"Failed to parse YAML agent file: {e}")
            return None
        
        if not isinstance(data, dict):
            logger.error(f"Invalid YAML agent format in {file_path}")
            return None
        
        return DeclarativeAgentDefinition(
            id=data.get("id", file_path.stem),
            name=data.get("name", ""),
            description=data.get("description", ""),
            system_prompt=data.get("system_prompt", data.get("systemPrompt", "")),
            skills=data.get("skills", []),
            tools=data.get("tools", []),
            model=data.get("model"),
            temperature=data.get("temperature"),
            source_path=file_path
        )
    
    def get_definition(self, agent_id: str) -> Optional[DeclarativeAgentDefinition]:
        """Get a loaded agent definition by ID."""
        return self._definitions.get(agent_id)
    
    def get_all(self) -> List[DeclarativeAgentDefinition]:
        """Get all loaded agent definitions."""
        return list(self._definitions.values())
