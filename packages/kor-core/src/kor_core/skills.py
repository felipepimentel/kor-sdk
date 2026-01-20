"""
Skills System for KOR SDK

Skills are reusable knowledge/procedures that agents can discover and apply.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path
import logging
from .search import SearchableRegistry
from .utils import parse_frontmatter, BaseLoader

logger = logging.getLogger(__name__)

@dataclass
class Skill:
    """
    A skill represents reusable knowledge or procedures.
    
    Skills are typically loaded from markdown files with YAML frontmatter.
    """
    name: str
    description: str
    content: str  # The actual skill content (instructions, knowledge)
    tags: List[str] = field(default_factory=list)
    source_path: Optional[Path] = None
    
    @property
    def searchable_text(self) -> str:
        """Combined text for search indexing."""
        return f"{self.name} {self.description} {' '.join(self.tags)} {self.content[:500]}"

    @classmethod
    def from_context_item(cls, item: "ContextItem") -> "Skill":
        """Factory to create a Skill from a ContextItem."""
        from .utils import parse_frontmatter
        frontmatter, body = parse_frontmatter(item.content)
        
        return cls(
            name=frontmatter.get("name", item.id),
            description=frontmatter.get("description", ""),
            content=body,
            tags=frontmatter.get("tags", []),
            source_path=Path(str(item.metadata.get("path", ""))) if item.metadata.get("path") else None
        )

class SkillRegistry(SearchableRegistry[Skill]):
    """
    Central registry for skills using the unified SearchableRegistry base.
    """
    
    def format_results(self, results: List[Skill], include_content: bool = False) -> str:
        """Format search results for the agent."""
        if not results:
            return "No matching skills found."
        
        lines = ["Available skills:"]
        for skill in results:
            lines.append(f"- **{skill.name}**: {skill.description}")
            if include_content:
                lines.append(f"  Content: {skill.content[:200]}...")
        return "\n".join(lines)


class SkillLoader(BaseLoader[Skill]):
    """
    Loads skills from directories.
    
    Expected file format:
    ```markdown
    ---
    name: skill-name
    description: What this skill does
    tags: [tag1, tag2]
    ---
    
    # Skill Content
    
    Instructions and knowledge here...
    ```
    """
    
    @property
    def file_patterns(self) -> List[str]:
        """File patterns to search for (default: *.md)."""
        return ["*.md", "SKILL.md"]

    def __init__(self, registry: Optional[SkillRegistry] = None):
        super().__init__()
        import warnings
        warnings.warn(
            "SkillLoader is deprecated and will be removed in v1.0. Use ContextManager with 'skill://' URI or SearchContextTool/GetContextTool instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.registry = registry or SkillRegistry()
    
    def get_key(self, item: Skill) -> str:
        return item.name

    def load_directory(self, directory: Path) -> List[Skill]:
        """Load all .md skills from a directory and register them."""
        # Using rglob to support subdirectories (Standard format uses folders)
        loaded = []
        if not directory.exists():
            return loaded

        # Walk manually to support both formats
        for file_path in directory.rglob("*.md"):
             if file_path.name == "SKILL.md":
                 # Standard format: directory name is skill name
                 pass
             try:
                skill = self.load_file(file_path)
                if skill:
                    self.registry.register(skill)
                    loaded.append(skill)
             except Exception as e:
                logger.error(f"Failed to load skill {file_path}: {e}")
                
        return loaded
    
    def load_file(self, file_path: Path) -> Optional[Skill]:
        """Load a single skill from a markdown file."""
        content = file_path.read_text()
        frontmatter, body = parse_frontmatter(content)
        
        name = frontmatter.get("name", file_path.stem)
        description = frontmatter.get("description", "")
        tags = frontmatter.get("tags", [])
        
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]
        
        return Skill(
            name=name,
            description=description,
            content=body,
            tags=tags,
            source_path=file_path
        )
    
    def load_from_config_dir(self) -> List[Skill]:
        """Load skills from ~/.kor/skills/ AND .agent/skills/"""
        loaded = []
        
        # 1. Global
        skills_dir = Path.home() / ".kor" / "skills"
        loaded.extend(self.load_directory(skills_dir))
        
        # 2. Project Standard
        # We try to detect the project root or assume CWD
        project_skills = Path.cwd() / ".agent" / "skills"
        if project_skills.exists():
             loaded.extend(self.load_directory(project_skills))
             
        return loaded
