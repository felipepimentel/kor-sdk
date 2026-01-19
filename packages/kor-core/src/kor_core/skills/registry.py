"""
Skills System for KOR

Skills are reusable knowledge/procedures that agents can discover and apply.
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Type
from pathlib import Path
import logging
from ..search import SearchBackend as SkillSearchBackend, RegexBackend as RegexSkillBackend, BM25Backend as BM25SkillBackend
from ..searchable_registry import SearchableRegistry

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
