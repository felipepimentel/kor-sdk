#!/usr/bin/env python3
"""
Search Symbols Script

Standalone script for searching code symbols.
Uses the CodeGraphDatabase for symbol lookup.
"""

import json
import sys
from pathlib import Path

# Add scripts directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

from graph import CodeGraphDatabase


def search_symbols(query: str) -> dict:
    """Search for symbols matching the query."""
    db_path = Path.home() / ".kor" / "codegraph.db"
    db = CodeGraphDatabase(db_path)
    
    results = db.search_symbols(query)
    
    if not results:
        return {"found": 0, "message": f"No symbols found for '{query}'.", "symbols": []}
    
    symbols = []
    for sym in results:
        symbols.append({
            "kind": sym.kind,
            "name": sym.name,
            "file": sym.file_path,
            "line": sym.line_start,
            "preview": sym.content_preview
        })
    
    return {"found": len(results), "symbols": symbols}


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: search_symbols.py <query> [--json]")
        sys.exit(1)
    
    query = sys.argv[1]
    result = search_symbols(query)
    
    if "--json" in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        if result["found"] == 0:
            print(result["message"])
        else:
            print(f"Found {result['found']} symbols for '{query}':")
            for sym in result["symbols"]:
                print(f"- [{sym['kind']}] {sym['name']} in {sym['file']}:{sym['line']}")
                print(f"  Preview: {sym['preview']}")


if __name__ == "__main__":
    main()
