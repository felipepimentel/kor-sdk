import logging
import asyncio
from pathlib import Path
from typing import List, Optional

from .protocols import ContextResolverProtocol
from .models import ContextQuery, ContextResult, ContextItem
from .exceptions import ContextError

logger = logging.getLogger(__name__)

class SkillResolver(ContextResolverProtocol):
    """
    Resolves skill://<name> URIs.
    
    Supports:
    1. Standard Folder: <path>/<name>/SKILL.md
    2. Legacy File: <path>/<name>.md
    
    Search Paths:
    - .agent/skills (Project Standard)
    - ~/.kor/skills (Global)
    """
    
    def __init__(self):
        self.search_paths: List[Path] = [
             Path.cwd() / ".agent" / "skills",
             Path.home() / ".kor" / "skills"
        ]
        
    def add_search_path(self, path: Path):
        """Add a path to the search list (high priority)."""
        if path not in self.search_paths:
            self.search_paths.insert(0, path)

    async def resolve(self, uri: str, query: ContextQuery) -> ContextResult:
        # uri = skill://python-mastery or skill:python-mastery
        try:
             # Strip scheme
            name = uri.split("skill://")[-1].split("skill:")[-1]
        except IndexError:
             raise ContextError(f"Invalid skill URI: {uri}")

        logger.debug(f"Resolving skill: {name}")
        
        # Search strategy
        for base_path in self.search_paths:
            if not base_path.exists():
                continue
                
            # 1. Standard: base/name/SKILL.md
            standard_path = base_path / name / "SKILL.md"
            if standard_path.exists():
                return await self._load_skill(standard_path, name)
                
            # 2. Legacy: base/name.md
            legacy_path = base_path / f"{name}.md"
            if legacy_path.exists():
                logger.warning(f"Loading legacy skill format for {name} from {legacy_path}")
                return await self._load_skill(legacy_path, name)
                
        raise ContextError(f"Skill not found: {name}")

    async def _load_skill(self, path: Path, name: str) -> ContextResult:
        """Load the skill content."""
        try:
            content = path.read_text()
            return ContextResult(
                items=[
                    ContextItem(
                        id=name,
                        content=content,
                        source_uri=f"file://{path}",
                        metadata={
                            "type": "skill", 
                            "path": str(path),
                            "format": "standard" if path.name == "SKILL.md" else "legacy"
                        }
                    )
                ]
            )
        except Exception as e:
            raise ContextError(f"Failed to read skill file {path}: {e}")
