"""
Skill Loader

Loads skills from filesystem directories (markdown files with YAML frontmatter).
"""

from pathlib import Path
from typing import List, Optional
import logging
from .registry import Skill, SkillRegistry

logger = logging.getLogger(__name__)

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """
    Parse YAML frontmatter from markdown content.
    
    Returns (frontmatter_dict, remaining_content)
    """
    frontmatter = {}
    body = content
    
    # Check for frontmatter delimiter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            import yaml
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
            except Exception:
                # If pyyaml not installed, try simple parsing
                for line in parts[1].strip().split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        value = value.strip()
                        # Handle list syntax [item1, item2]
                        if value.startswith("[") and value.endswith("]"):
                            value = [v.strip().strip('"\'') for v in value[1:-1].split(",")]
                        frontmatter[key.strip()] = value
            body = parts[2].strip()
    
    return frontmatter, body

class SkillLoader:
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
        self.registry = registry or SkillRegistry()
    
    def load_directory(self, directory: Path) -> List[Skill]:
        """Load all .md skills from a directory."""
        loaded = []
        
        if not directory.exists():
            logger.debug(f"Skills directory does not exist: {directory}")
            return loaded
        
        for file_path in directory.glob("*.md"):
            try:
                skill = self.load_file(file_path)
                if skill:
                    self.registry.register(skill)
                    loaded.append(skill)
                    logger.info(f"Loaded skill: {skill.name}")
            except Exception as e:
                logger.error(f"Failed to load skill from {file_path}: {e}")
        
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
