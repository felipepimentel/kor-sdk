#!/usr/bin/env python3
"""
Token Tracker Script

Tracks token usage for LLM calls. Stores data in SQLite.
"""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


def get_db_path() -> Path:
    """Get the token tracking database path."""
    return Path.home() / ".kor" / "token_usage.db"


def init_db():
    """Initialize the database with required tables."""
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS token_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            session_id TEXT,
            model TEXT,
            provider TEXT,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            total_tokens INTEGER,
            cost_estimate REAL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            max_tokens INTEGER,
            period TEXT,  -- 'hourly', 'daily', 'session'
            current_usage INTEGER DEFAULT 0,
            reset_at TEXT
        )
    """)
    
    conn.commit()
    conn.close()


def track_usage(data: dict):
    """Record token usage from an LLM call."""
    init_db()
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO token_usage 
        (timestamp, session_id, model, provider, prompt_tokens, completion_tokens, total_tokens, cost_estimate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        data.get("session_id"),
        data.get("model"),
        data.get("provider"),
        data.get("prompt_tokens", 0),
        data.get("completion_tokens", 0),
        data.get("total_tokens", 0),
        data.get("cost_estimate", 0.0)
    ))
    
    conn.commit()
    conn.close()


def get_usage_summary(period: str = "daily") -> dict:
    """Get token usage summary for a period."""
    init_db()
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    if period == "daily":
        date_filter = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT 
                COUNT(*) as calls,
                COALESCE(SUM(prompt_tokens), 0) as prompt_tokens,
                COALESCE(SUM(completion_tokens), 0) as completion_tokens,
                COALESCE(SUM(total_tokens), 0) as total_tokens,
                COALESCE(SUM(cost_estimate), 0) as total_cost
            FROM token_usage
            WHERE timestamp LIKE ?
        """, (f"{date_filter}%",))
    else:
        cursor.execute("""
            SELECT 
                COUNT(*) as calls,
                COALESCE(SUM(prompt_tokens), 0) as prompt_tokens,
                COALESCE(SUM(completion_tokens), 0) as completion_tokens,
                COALESCE(SUM(total_tokens), 0) as total_tokens,
                COALESCE(SUM(cost_estimate), 0) as total_cost
            FROM token_usage
        """)
    
    row = cursor.fetchone()
    conn.close()
    
    return {
        "period": period,
        "calls": row[0],
        "prompt_tokens": row[1],
        "completion_tokens": row[2],
        "total_tokens": row[3],
        "estimated_cost": round(row[4], 4)
    }


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: tracker.py [track|summary|init]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "init":
        init_db()
        print("Token tracking database initialized.")
        
    elif cmd == "track":
        # Expects JSON input via stdin or argv
        if len(sys.argv) > 2:
            data = json.loads(sys.argv[2])
        else:
            data = json.loads(sys.stdin.read())
        track_usage(data)
        print("Usage tracked.")
        
    elif cmd == "summary":
        period = sys.argv[2] if len(sys.argv) > 2 else "daily"
        summary = get_usage_summary(period)
        print(json.dumps(summary, indent=2))
        
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
