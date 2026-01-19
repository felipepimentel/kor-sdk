import logging
from kor_core import KorPlugin, KorContext
from kor_core.tools.registry import ToolRegistry
from kor_core.skills.registry import SkillRegistry
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
        
        logger.info("Registered 'semantic' search backend for Tools and Skills.")
