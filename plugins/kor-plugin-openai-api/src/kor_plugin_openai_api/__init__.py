"""
KOR OpenAI-Compatible API Plugin

Exposes KOR agents via an OpenAI-compatible REST API.
"""

from .main import app, run

__all__ = ["app", "run"]
