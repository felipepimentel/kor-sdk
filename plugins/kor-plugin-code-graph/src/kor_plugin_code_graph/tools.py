from pathlib import Path
from kor_core.tools import KorTool
from .graph import CodeGraphDatabase
from .indexer import CodeIndexer
import os

class SearchSymbolsTool(KorTool):
    name: str = "search_symbols"
    description: str = "Search for classes or functions in the codebase semantically. Returns file paths and line numbers."
    
    def _run(self, query: str) -> str:
        # TODO: Get DB path from context/config?
        # For MVP we use a fixed hidden path in home
        db_path = Path.home() / ".kor" / "codegraph.db"
        
        db = CodeGraphDatabase(db_path)
        
        # Trigger explicit scan on search? Or rely on background?
        # For immediate feedback in this MVP, we might want to lazy-trigger scan of root?
        # But we don't know the root here easily without context injecting it.
        # We assume the index is fresh or we construct Indexer if we can.
        
        # Let's search
        results = db.search_symbols(query)
        
        if not results:
            return f"No symbols found for '{query}'."
            
        output = f"Found {len(results)} symbols for '{query}':\n"
        for sym in results:
            output += f"- [{sym.kind}] {sym.name} in {sym.file_path}:{sym.line_start}\n"
            output += f"  Preview: {sym.content_preview}\n"
            
        return output

class GetSymbolDefinitionTool(KorTool):
    name: str = "get_symbol_definition"
    description: str = "Get the full source code calculation/definition of a specific symbol. Use this to read the implementation details."
    
    def _run(self, symbol_name: str) -> str:
        db_path = Path.home() / ".kor" / "codegraph.db"
        db = CodeGraphDatabase(db_path)
        
        # We search for exact match first, then fuzzy
        # This is a bit naive, but works for now.
        # Ideally we'd pass a file_path too to disambiguate.
        results = db.search_symbols(symbol_name)
        
        target = None
        for r in results:
            if r.name == symbol_name:
                target = r
                break
        
        if not target and results:
            target = results[0] # Fallback to first
            
        if not target:
            return f"Symbol '{symbol_name}' not found."
            
        try:
            # Read the file content
            path = Path(target.file_path)
            if not path.exists():
                return f"File {path} no longer exists."
                
            lines = path.read_text(errors='ignore').splitlines()
            
            # 1-indexed to 0-indexed
            start = max(0, target.line_start - 1)
            end = target.line_end # exclusive in slice? No, line_end is inclusive in tree-sitter logic usually?
            # Tree-sitter 1-indexed lines are usually inclusive. 
            # In indexer.py: line_end = node.end_point[0] + 1. 
            # slice is [start:end].
            
            definition = "\n".join(lines[start:end])
            
            return f"Definition of '{target.name}' in {target.file_path}:\n```python\n{definition}\n```"
        except Exception as e:
            return f"Error reading definition: {e}"
