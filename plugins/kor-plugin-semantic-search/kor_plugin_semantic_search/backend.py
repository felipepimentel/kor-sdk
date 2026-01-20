import logging
from typing import List, Dict, Optional, Any
from kor_core.search import SearchBackend, T, VectorStoreProtocol

logger = logging.getLogger(__name__)

class ChromaDBBackend(SearchBackend[T], VectorStoreProtocol):
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

        return found_items

    # ==========================
    # VectorStoreProtocol Impl
    # ==========================
    
    def add(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None, ids: Optional[List[str]] = None) -> None:
        self._ensure_initialized()
        
        count = len(texts)
        if not ids:
             import uuid
             ids = [str(uuid.uuid4()) for _ in range(count)]
             
        if not metadatas:
             metadatas = [{} for _ in range(count)]
             
        self._collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Added {count} text items to ChromaDB vector store.")

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Overloaded search:
        - If used as SearchBackend, returns List[T] (but strict typing might complain if we mix protocols).
        - Actually, VectorStoreProtocol.search returns List[Dict]. SearchBackend.search returns List[T].
        - This is a conflict if we try to be strict. 
        - Runtime is fine because arguments differ? No, arguments are same (query, top_k).
        
        Strategy: Since this class is used as a backend factory mostly, the instances are separate?
        No, SkillRegistry instantiates one.
        
        The plugin uses this class for TWO purposes:
        1. Registry Backend (Indexing existing python objects)
        2. General Vector Store (Storing arbitrary text for Context)
        
        If we call search() looking for Objects, we rely on self._items.
        If we call search() looking for Text (VectorStore), we don't have _items.
        
        Refactor: We should use a different method name or check if self._items is populated.
        But SearchBackend defines search(). VectorStoreProtocol defines search().
        
        Let's RENAME the VectorStoreProtocol method in the Protocol definition? NO, standard.
        
        Let's allow this method to return EITHER based on internal state? 
        Or better, let's implement VectorStoreProtocol in a SEPARATE class or Adapter.
        """
        # FOR NOW: We assume if _items is populated, we are acting as Object Registry Backend.
        # If _items is empty, we act as pure Vector Store.
        
        self._ensure_initialized()
        
        results = self._collection.query(
            query_texts=[query],
            n_results=top_k 
        )
        
        # Case A: Object Search (SearchBackend)
        if self._items:
            found_items = []
            if results["ids"]:
                for meta in results["metadatas"][0]:
                    idx = meta.get("index") # Only registries set 'index'
                    if idx is not None and 0 <= idx < len(self._items):
                        found_items.append(self._items[idx])
            return found_items

        # Case B: Text Search (VectorStoreProtocol)
        # Flatten results
        found_dicts = []
        if results["ids"]:
            ids = results["ids"][0]
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            
            for i in range(len(ids)):
                found_dicts.append({
                    "id": ids[i],
                    "text": docs[i] if docs else "",
                    "metadata": metas[i] if metas else {}
                })
                
        return found_dicts
