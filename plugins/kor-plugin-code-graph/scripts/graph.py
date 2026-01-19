import sqlite3
import logging
from typing import List, Optional, NamedTuple
from pathlib import Path

logger = logging.getLogger(__name__)

class Symbol(NamedTuple):
    name: str
    kind: str
    file_path: str
    line_start: int
    line_end: int
    content_preview: str

class CodeGraphDatabase:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Table: Files (Merkle tracking)
        c.execute('''
            CREATE TABLE IF NOT EXISTS files (
                path TEXT PRIMARY KEY,
                hash TEXT NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table: Symbols
        c.execute('''
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                kind TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line_start INTEGER,
                line_end INTEGER,
                preview TEXT,
                FOREIGN KEY(file_path) REFERENCES files(path) ON DELETE CASCADE
            )
        ''')
        # Index for search
        c.execute('CREATE INDEX IF NOT EXISTS idx_symbol_name ON symbols(name)')
        
        conn.commit()
        conn.close()

    def get_file_hash(self, path: str) -> Optional[str]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT hash FROM files WHERE path = ?", (path,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None

    def upsert_file_symbols(self, path: str, file_hash: str, symbols: List[Symbol]):
        """Atomic upsert of a file and its symbols."""
        conn = sqlite3.connect(self.db_path)
        try:
            c = conn.cursor()
            
            # 1. Update File
            c.execute("INSERT OR REPLACE INTO files (path, hash) VALUES (?, ?)", (path, file_hash))
            
            # 2. Clear old symbols for this file
            c.execute("DELETE FROM symbols WHERE file_path = ?", (path,))
            
            # 3. Insert new symbols
            for sym in symbols:
                c.execute('''
                    INSERT INTO symbols (name, kind, file_path, line_start, line_end, preview)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (sym.name, sym.kind, path, sym.line_start, sym.line_end, sym.content_preview))
            
            conn.commit()
        except Exception as e:
            logger.error(f"DB Error upserting {path}: {e}")
            conn.rollback()
        finally:
            conn.close()

    def search_symbols(self, query: str) -> List[Symbol]:
        """Fuzzy search for symbols."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Simple LIKE query for now
        like_query = f"%{query}%"
        c.execute('''
            SELECT name, kind, file_path, line_start, line_end, preview
            FROM symbols
            WHERE name LIKE ?
            ORDER BY length(name) ASC 
            LIMIT 20
        ''', (like_query,))
        
        results = []
        for row in c.fetchall():
            results.append(Symbol(*row))
            
        conn.close()
        return results
