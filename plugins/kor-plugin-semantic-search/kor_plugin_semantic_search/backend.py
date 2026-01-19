import logging
from typing import List, TypeVar, Any
from kor_core.search import SearchBackend, T

logger = logging.getLogger(__name__)

class ChromaDBBackend(SearchBackend[T]):
    """
    Semantic search backend utilizing ChromaDB and Sentence Transformers.
    """
    
    def __init__(self, collection_name: str = "kor_index"):
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._items: List[T] = []
        self._initialized = False

    def _ensure_initialized(self):
        if self._initialized:
            return
            
        try:
            import chromadb
            from chromadb.utils import embedding_functions
            
            # Use persistent storage if desired, or ephemeral for now
            self._client = chromadb.Client()
            
            # Default to a lightweight local model
            ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=ef
            )
            self._initialized = True
            logger.info(f"ChromaDB backend initialized with collection '{self.collection_name}'")
            
        except ImportError:
            logger.error("ChromaDB or sentence-transformers not installed. Install 'kor-plugin-semantic-search' dependencies.")
            raise

    def index(self, items: List[T]) -> None:
        """
        Index items using their searchable_text.
        """
        self._ensure_initialized()
        self._items = items # Keep reference map results back to objects
        
        if not items:
            return

        documents = [item.searchable_text for item in items]
        ids = [str(i) for i in range(len(items))] # Simple index-based IDs
        metadatas = [{"index": i} for i in range(len(items))]
        
        # Reset collection to avoid stale data (simple strategy for V1)
        try:
             self._client.delete_collection(self.collection_name)
             import chromadb
             from chromadb.utils import embedding_functions
             ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
             )
             self._collection = self._client.create_collection(
                 name=self.collection_name, 
                 embedding_function=ef
             )
        except Exception as e:
            logger.warning(f"Could not reset collection, upserting instead: {e}")

        # Batch add? Chroma handles it well usually.
        self._collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Indexed {len(items)} items in ChromaDB.")

    def search(self, query: str, top_k: int = 5) -> List[T]:
        """
        Search for items matching the query semantically.
        """
        self._ensure_initialized()
        if not self._items:
            return []

        results = self._collection.query(
            query_texts=[query],
            n_results=min(top_k, len(self._items))
        )
        
        # Chroma returns list of lists (one per query)
        found_items = []
        if results["ids"]:
            # results["metadatas"][0] contains list of dicts like {'index': 0}
            for meta in results["metadatas"][0]:
                idx = meta["index"]
                if 0 <= idx < len(self._items):
                    found_items.append(self._items[idx])
                    
        return found_items
