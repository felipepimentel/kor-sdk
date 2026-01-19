import pytest
import sys
from unittest.mock import MagicMock, patch
from kor_core.tools.registry import ToolRegistry

# We need to simulate the plugin loading process or just manually call the registration
# Since we are testing if the plugin *code* works, we can just import it.

# But first, we must mock chromadb and sentence-transformers if not present
mock_chroma = MagicMock()
mock_st = MagicMock()

@patch.dict("sys.modules", {"chromadb": mock_chroma, "chromadb.utils": MagicMock(), "sentence_transformers": mock_st})
def test_semantic_search_plugin_registration():
    """Verify the plugin registers the backend to ToolRegistry."""
    # Temporarily add plugin path to sys.path to simulate install? 
    # Or just use relative import if we are in root.
    # The plugin is in plugins/kor-plugin-semantic-search/kor_plugin_semantic_search
    
    # Let's try to import the backend class directly from source file
    
    # Mocking the backend module requires the file to be importaable.
    # Since it's not installed in venv, we add it to path for test
    import os
    plugin_path = os.path.abspath("plugins/kor-plugin-semantic-search")
    if plugin_path not in sys.path:
        sys.path.insert(0, plugin_path)
        
    try:
        from kor_plugin_semantic_search.plugin import SemanticSearchPlugin
        from kor_plugin_semantic_search.backend import ChromaDBBackend
        from kor_core.tools.registry import ToolRegistry
        
        # 1. Instantiate Plugin
        plugin = SemanticSearchPlugin()
        context = MagicMock()
        
        # 2. Run Initialize
        plugin.initialize(context)
        
        # 3. Verify Registry has 'semantic'
        assert "semantic" in ToolRegistry.BACKENDS
        assert ToolRegistry.BACKENDS["semantic"] == ChromaDBBackend
        
    finally:
        if plugin_path in sys.path:
            sys.path.remove(plugin_path)

@patch.dict("sys.modules", {"chromadb": mock_chroma, "chromadb.utils": MagicMock()})
def test_backend_indexing():
    """Verify backend logic calls ChromaDB."""
    import os
    plugin_path = os.path.abspath("plugins/kor-plugin-semantic-search")
    if plugin_path not in sys.path:
        sys.path.insert(0, plugin_path)
        
    from kor_plugin_semantic_search.backend import ChromaDBBackend
    
    backend = ChromaDBBackend(collection_name="test_col")
    
    # Mock inner client
    backend._client = MagicMock()
    backend._collection = MagicMock()
    backend._initialized = True # Skip real init
    
    # Create dummy items
    item1 = MagicMock()
    item1.searchable_text = "doc1"
    
    backend.index([item1])
    
    # Verify add called
    backend._collection.add.assert_called_once()
    args, kwargs = backend._collection.add.call_args
    assert kwargs['documents'] == ["doc1"]
    assert kwargs['ids'] == ["0"]
