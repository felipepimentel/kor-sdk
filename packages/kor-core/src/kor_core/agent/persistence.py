"""
Persistence utility for KOR agents using LangGraph SqliteSaver.
"""
import os
import sqlite3
from pathlib import Path
from typing import Optional
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.sqlite import SqliteSaver
from ..config import PersistenceConfig

def get_checkpointer(config: PersistenceConfig) -> BaseCheckpointSaver:
    """
    Returns a CheckpointSaver based on configuration.
    """
    if config.type == "memory":
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()
    
    elif config.type == "sqlite":
        # Default path: ~/.kor/memories.db if not defined
        db_path = config.path
        if not db_path:
            home = Path.home()
            kor_dir = home / ".kor"
            kor_dir.mkdir(exist_ok=True)
            db_path = str(kor_dir / "memories.db")
            
        conn = sqlite3.connect(db_path, check_same_thread=False)
        return SqliteSaver(conn)
        
    else:
        # Fallback to internal memory if unknown
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()
