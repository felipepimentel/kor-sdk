"""
Persistence utility for KOR agents using LangGraph SqliteSaver.
"""
import os
import sqlite3
from pathlib import Path
from typing import Optional
from langgraph.checkpoint.sqlite import SqliteSaver

def get_sqlite_checkpointer(db_path: Optional[str] = None) -> SqliteSaver:
    """
    Returns a SqliteSaver checkpointer.
    
    Default path: ~/.kor/memories.db
    """
    if not db_path:
        home = Path.home()
        kor_dir = home / ".kor"
        kor_dir.mkdir(exist_ok=True)
        db_path = str(kor_dir / "memories.db")
        
    # LangGraph SqliteSaver expects a connection pool or a path
    # For simplicity, we use a connection that we keep open
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return SqliteSaver(conn)
