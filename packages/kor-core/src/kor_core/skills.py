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
    
    def __init__(self, registry: Optional[SkillRegistry] = None):
        super().__init__()
        self.registry = registry or SkillRegistry()
    
    def get_key(self, item: Skill) -> str:
        return item.name

    def load_directory(self, directory: Path) -> List[Skill]:
        """Load all .md skills from a directory and register them."""
        loaded = super().load_directory(directory)
        for skill in loaded:
            self.registry.register(skill)
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
        """Load skills from ~/.kor/skills/"""
        skills_dir = Path.home() / ".kor" / "skills"
        return self.load_directory(skills_dir)
