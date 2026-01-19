import threading
import os
from pathlib import Path
from kor_core.plugin import KorPlugin, KorContext
from .tools import SearchSymbolsTool
from .graph import CodeGraphDatabase
from .indexer import CodeIndexer

class CodeGraphPlugin(KorPlugin):
    @property
    def id(self) -> str:
        return "kor-plugin-code-graph"

    def initialize(self, context: KorContext) -> None:
        # Register Tool
        registry = context.registry.get_service("tools")
        if registry:
            registry.register_class(SearchSymbolsTool, tags=["search", "code", "symbol"])
            
        # Start Indexing in Background
        # We assume CWD is the project root for now
        root = Path(os.getcwd())
        db_path = Path.home() / ".kor" / "codegraph.db"
        
        def run_indexer():
            try:
                db = CodeGraphDatabase(db_path)
                indexer = CodeIndexer(db, root)
                indexer.scan_workspace()
            except Exception as e:
                # Log error
                pass

        thread = threading.Thread(target=run_indexer, daemon=True)
        thread.start()
