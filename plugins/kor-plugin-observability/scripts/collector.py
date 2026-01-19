#!/usr/bin/env python3
"""
Metrics Collector Script

Collects and stores metrics for agents, tools, and sessions.
"""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


def get_db_path() -> Path:
    """Get the metrics database path."""
    return Path.home() / ".kor" / "metrics.db"


def init_db():
    """Initialize the database with required tables."""
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_name TEXT NOT NULL,
            session_id TEXT,
            agent_id TEXT,
            tool_name TEXT,
            duration_ms INTEGER,
            success INTEGER,
            metadata TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            message_count INTEGER DEFAULT 0,
            tool_calls INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active'
        )
    """)
    
    conn.commit()
    conn.close()


def record_event(event_type: str, event_name: str, data: dict = None):
    """Record a single event."""
    init_db()
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    data = data or {}
    
    cursor.execute("""
        INSERT INTO events 
        (timestamp, event_type, event_name, session_id, agent_id, tool_name, duration_ms, success, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        event_type,
        event_name,
        data.get("session_id"),
        data.get("agent_id"),
        data.get("tool_name"),
        data.get("duration_ms"),
        1 if data.get("success", True) else 0,
        json.dumps(data.get("metadata", {}))
    ))
    
    conn.commit()
    conn.close()


def get_metrics_summary() -> dict:
    """Get overall metrics summary."""
    init_db()
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Count events by type
    cursor.execute("""
        SELECT event_type, COUNT(*) 
        FROM events 
        WHERE timestamp > datetime('now', '-24 hours')
        GROUP BY event_type
    """)
    event_counts = dict(cursor.fetchall())
    
    # Count sessions
    cursor.execute("SELECT COUNT(*) FROM sessions WHERE status = 'active'")
    active_sessions = cursor.fetchone()[0]
    
    # Average tool duration
    cursor.execute("""
        SELECT AVG(duration_ms) 
        FROM events 
        WHERE event_type = 'tool_call' AND duration_ms IS NOT NULL
    """)
    avg_tool_duration = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        "period": "24h",
        "event_counts": event_counts,
        "active_sessions": active_sessions,
        "avg_tool_duration_ms": round(avg_tool_duration, 2)
    }


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: collector.py [init|record|summary]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "init":
        init_db()
        print("Metrics database initialized.")
        
    elif cmd == "record":
        # record <event_type> <event_name> [json_data]
        if len(sys.argv) < 4:
            print("Usage: collector.py record <event_type> <event_name> [json_data]")
            sys.exit(1)
        event_type = sys.argv[2]
        event_name = sys.argv[3]
        data = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
        record_event(event_type, event_name, data)
        print(f"Recorded: {event_type}/{event_name}")
        
    elif cmd == "summary":
        summary = get_metrics_summary()
        print(json.dumps(summary, indent=2))
        
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
