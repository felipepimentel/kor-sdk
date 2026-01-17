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

class SkillSearchBackend(ABC):
    """Abstract base for skill search backends."""
    
    @abstractmethod
    def index(self, skills: List[Skill]) -> None:
        pass
    
    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[Skill]:
        pass

class RegexSkillBackend(SkillSearchBackend):
    """Simple regex/keyword matching backend for skills."""
    
    def __init__(self):
        self._skills: List[Skill] = []
    
    def index(self, skills: List[Skill]) -> None:
        self._skills = skills
    
    def search(self, query: str, top_k: int = 5) -> List[Skill]:
        query_lower = query.lower()
        query_words = set(re.findall(r'\w+', query_lower))
        
        scored = []
        for skill in self._skills:
            text = skill.searchable_text.lower()
            matches = sum(1 for word in query_words if word in text)
            if matches > 0:
                scored.append((matches, skill))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [skill for _, skill in scored[:top_k]]

class BM25SkillBackend(SkillSearchBackend):
    """BM25 ranking backend for skills."""
    
    def __init__(self):
        self._skills: List[Skill] = []
        self._bm25 = None
    
    def index(self, skills: List[Skill]) -> None:
        self._skills = skills
        
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            raise ImportError("rank-bm25 is required. Install with: pip install rank-bm25")
        
        tokenized_corpus = [skill.searchable_text.lower().split() for skill in skills]
        self._bm25 = BM25Okapi(tokenized_corpus)
    
    def search(self, query: str, top_k: int = 5) -> List[Skill]:
        if not self._bm25:
            return []
        
        tokenized_query = query.lower().split()
        scores = self._bm25.get_scores(tokenized_query)
        
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, score in indexed_scores[:top_k]:
            if score > 0:
                results.append(self._skills[idx])
        
        return results

class SkillRegistry:
    """
    Central registry for skills with pluggable search backend.
    
    Usage:
        registry = SkillRegistry(backend="bm25")
        registry.register(Skill(name="pytest", description="...", content="..."))
        results = registry.search("unit testing")
    """
    
    BACKENDS = {
        "regex": RegexSkillBackend,
        "bm25": BM25SkillBackend,
    }
    
    def __init__(self, backend: str = "regex"):
        if backend not in self.BACKENDS:
            raise ValueError(f"Unknown backend: {backend}")
        
        self._backend: SkillSearchBackend = self.BACKENDS[backend]()
        self._skills: Dict[str, Skill] = {}
        self._indexed = False
    
    def register(self, skill: Skill) -> None:
        """Register a skill."""
        self._skills[skill.name] = skill
        self._indexed = False
    
    def _ensure_indexed(self) -> None:
        if not self._indexed:
            self._backend.index(list(self._skills.values()))
            self._indexed = True
    
    def search(self, query: str, top_k: int = 5) -> List[Skill]:
        """Search for skills matching the query."""
        self._ensure_indexed()
        return self._backend.search(query, top_k)
    
    def get(self, name: str) -> Optional[Skill]:
        """Get a skill by name."""
        return self._skills.get(name)
    
    def get_all(self) -> List[Skill]:
        """Get all registered skills."""
        return list(self._skills.values())
    
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

# Extension point for semantic backend
def register_semantic_skill_backend(backend_class: Type[SkillSearchBackend]) -> None:
    """Register a custom semantic search backend for skills."""
    SkillRegistry.BACKENDS["semantic"] = backend_class
