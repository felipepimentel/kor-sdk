"""
Hooks Module

Provides declarative hooks loading from hooks.json files.
"""

from .loader import HooksLoader, DeclarativeAction

__all__ = ["HooksLoader", "DeclarativeAction"]
