"""
Data models for the Context System.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import datetime

@dataclass
class ContextQuery:
    """
    Represents a request for context.
    """
    uri: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    
@dataclass
class ContextItem:
    """
    A single unit of context (e.g., a Skill, a Document, a Configuration).
    """
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_uri: Optional[str] = None
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class ContextResult:
    """
    The result of a context resolution.
    """
    items: List[ContextItem] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
