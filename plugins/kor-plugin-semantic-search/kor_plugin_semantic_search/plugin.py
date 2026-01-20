import logging
from kor_core import KorPlugin, KorContext
from kor_core.tools.registry import ToolRegistry
from kor_core.skills import SkillRegistry
from .backend import ChromaDBBackend

logger = logging.getLogger(__name__)

class SemanticSearchPlugin(KorPlugin):
    id = "semantic-search"
    
    def initialize(self, context: KorContext):
        logger.info("Initializing Semantic Search Plugin...")
        
        # Register the backend class for Tools
        # The registry will instantiate it when 'semantic' backend is requested
        ToolRegistry.register_semantic_backend(ChromaDBBackend)
        
        # Register for Skills
        SkillRegistry.register_semantic_backend(ChromaDBBackend)
        
        # Register as Singleton Vector Store Service
        # We need to instantiate it specifically for this purpose
        vector_store = ChromaDBBackend(collection_name="kor_project_memory")
        context.registry.register_service("vector_store", vector_store)
        
        logger.info("Registered 'semantic' search backend and 'vector_store' service.")
