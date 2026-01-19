import hashlib
import logging
from pathlib import Path
from typing import List, Optional
from .graph import CodeGraphDatabase, Symbol

logger = logging.getLogger(__name__)

# Try importing Tree Sitter
try:
    from tree_sitter import Language, Parser
    import tree_sitter_python as tspython
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    logger.warning("Tree Sitter not found. Indexing will mean nothing (or fallback to regex).")

class CodeIndexer:
    def __init__(self, db: CodeGraphDatabase, project_root: Path):
        self.db = db
        self.root = project_root
        
        self.parser = None
        if TREE_SITTER_AVAILABLE:
            try:
                # API Variation: Try using the language object directly from the binding
                # Recent versions of tree-sitter-languages return the object ready to use
                self.parser = Parser()
                try:
                    # Attempt 1: Wrap in Language (old way)
                    lang = Language(tspython.language())
                except:
                    # Attempt 2: Use directly
                    lang = tspython.language()
                    
                self.parser.set_language(lang)
            except Exception as e:
                logger.error(f"Failed to init Tree Sitter: {e}")

    def scan_workspace(self):
        """Scans all supported files and updates the index."""
        logger.info(f"Scanning workspace: {self.root}")
        for path in self.root.rglob("*.py"):
            if "site-packages" in str(path) or ".venv" in str(path) or "node_modules" in str(path):
                continue
            self._process_file(path)

    def _process_file(self, path: Path):
        try:
            content = path.read_text(errors='ignore')
            file_hash = hashlib.md5(content.encode()).hexdigest()
            
            # Check DB cache
            cached_hash = self.db.get_file_hash(str(path))
            if cached_hash == file_hash:
                return # Unchanged

            # Parse Symbols
            symbols = self._extract_symbols(path, content)
            
            # Update DB
            self.db.upsert_file_symbols(str(path), file_hash, symbols)
            logger.debug(f"Indexed {path} ({len(symbols)} symbols)")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Error processing {path}: {e}")

    def _extract_symbols(self, path: Path, content: str) -> List[Symbol]:
        symbols = []
        
        # Try Tree Sitter
        if self.parser:
            try:
                tree = self.parser.parse(bytes(content, "utf8"))
                cursor = tree.walk()
                
                def visit(node):
                    if node.type in ["class_definition", "function_definition"]:
                        name_node = node.child_by_field_name("name")
                        if name_node:
                            # Verify bounds
                            if name_node.end_byte <= len(content):
                                original_name = content[name_node.start_byte:name_node.end_byte]
                                line_start = node.start_point[0] + 1
                                line_end = node.end_point[0] + 1
                                preview = content[node.start_byte:node.end_byte].split('\n')[0]
                                
                                symbols.append(Symbol(
                                    name=original_name,
                                    kind=node.type,
                                    file_path=str(path),
                                    line_start=line_start,
                                    line_end=line_end,
                                    content_preview=preview
                                ))
                    
                    for child in node.children:
                        visit(child)
                        
                visit(tree.root_node)
                return symbols
            except Exception as e:
                logger.warning(f"Tree Sitter parse failed for {path}: {e}. Falling back to Regex.")
                # Fall through to regex
        
        # Regex Fallback
        import re
        lines = content.splitlines()
        for i, line in enumerate(lines):
            line_num = i + 1
            stripped = line.strip()
            kind = None
            name = None
            
            # Simple heuristic: Only top-level or method defs
            # We preserve indentation context if needed, but for now simple scan
            if stripped.startswith("class "):
                match = re.search(r"class\s+([a-zA-Z0-9_]+)", line)
                if match:
                    kind = "class_definition"
                    name = match.group(1)
            elif stripped.startswith("def "):
                match = re.search(r"def\s+([a-zA-Z0-9_]+)", line)
                if match:
                    kind = "function_definition"
                    name = match.group(1)
            
            if name and kind:
                symbols.append(Symbol(
                    name=name,
                    kind=kind,
                    file_path=str(path),
                    line_start=line_num,
                    line_end=line_num, # We don't know end easily in regex
                    content_preview=line
                ))
                
        return symbols
