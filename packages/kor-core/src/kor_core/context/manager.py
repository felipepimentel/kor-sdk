"""
Context Manager (Orchestrator).
"""
import logging
from typing import Dict, Any, Optional, Type
from urllib.parse import urlparse
from pathlib import Path

from .models import ContextQuery, ContextResult
from .protocols import ContextResolverProtocol, ContextSourceProtocol
from .exceptions import ResolverNotFoundError, ContextError

logger = logging.getLogger(__name__)

class ContextManager:
    """
    Singleton orchestrator for the Context System.
    Manages resolvers, sources, and context acquisition/persistence.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ContextManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Prevent re-initialization if already initialized in __new__
        if not hasattr(self, "resolvers"):
            self.resolvers: Dict[str, ContextResolverProtocol] = {}
            self.schemes: Dict[str, str] = {} # scheme -> resolver_id
            self.mappings: Dict[str, str] = {} # Config mappings
            self.project_mappings: Dict[str, str] = {} # Auto-detected mappings
            
            # Default Resolvers
            from .resolvers import LocalResolver, GitResolver, ScriptResolver
            from .skills import SkillResolver
            from .mcp import MCPResolver
            
            self.register_resolver("local", LocalResolver())
            self.register_resolver("git", GitResolver())
            self.register_resolver("run", ScriptResolver())
            self.register_resolver("skill", SkillResolver())
            self.register_resolver("mcp", MCPResolver())
            
            # Auto-detect project context on boot
            self.detect_project_context()

    def detect_project_context(self, root_dir: Path = None):
        """Auto-detect project context structure."""
        from pathlib import Path
        from .project import ProjectContextDetector
        
        try:
            self.project_mappings = ProjectContextDetector.detect(root_dir)
            if self.project_mappings:
                logger.debug(f"Loaded {len(self.project_mappings)} context mappings from project detection")
        except Exception as e:
            logger.warning(f"Failed to detect project context: {e}")

    def register_resolver(self, scheme: str, resolver: ContextResolverProtocol):
        """Register a resolver for a specific URI scheme."""
        logger.info(f"Registering context resolver for scheme: {scheme}")
        self.resolvers[scheme] = resolver
        self.schemes[scheme] = scheme

    def get_resolver(self, scheme: str) -> Optional[ContextResolverProtocol]:
        """Get the resolver for a scheme."""
        return self.resolvers.get(scheme)

    async def resolve(self, uri: str, parameters: Dict[str, Any] = None) -> ContextResult:
        """
        Resolve a URI to a ContextResult.
        
        Args:
            uri: The context URI (e.g., 'jira://PROJ-123', 'git://...', 'local://...')
            parameters: Optional query parameters.
            
        Returns:
            ContextResult containing the fetched items.
            
        Raises:
            ResolverNotFoundError: If no resolver is registered for the scheme.
            ContextError: If resolution fails.
        """
        # 1. Apply Mappings (Redirections)
        uri = self._apply_mapping(uri)
        
        parsed = urlparse(uri)
        scheme = parsed.scheme
        
        # If no scheme, assume 'local' (Simple & Basic Default)
        if not scheme:
            # Default to local scheme
            logger.debug(f"No scheme found in '{uri}', defaulting to 'local://'")
            uri = f"local://{uri}"
            parsed = urlparse(uri)
            scheme = parsed.scheme
            
        if not scheme:
             # Should not happen after default, but safe fallback
             raise ContextError(f"Invalid URI format (missing scheme): {uri}")

        resolver = self.get_resolver(scheme)
        if not resolver:
            raise ResolverNotFoundError(f"No resolver registered for scheme: {scheme}")

        query = ContextQuery(uri=uri, parameters=parameters or {})
        
        try:
            logger.debug(f"Resolving URI: {uri} with scheme {scheme}")
            result = await resolver.resolve(uri, query)
            return result
        except Exception as e:
            logger.error(f"Context resolution failed for {uri}: {e}")
            raise ContextError(f"Resolution failed for {uri}: {e}") from e

    def load_config(self, config: Dict[str, str]):
        """Load context mappings from configuration."""
        self.mappings = config
        logger.info(f"Loaded {len(self.mappings)} context mappings from config")

    def _apply_mapping(self, uri: str) -> str:
        """
        Apply configuration and project mappings to the URI.
        Supports exact match and simple wildcard suffixes.
        Priority: Config > Project
        """
        # 1. Config Exact Match
        if hasattr(self, "mappings") and uri in self.mappings:
            return self.mappings[uri]
            
        # 2. Project Exact Match
        if hasattr(self, "project_mappings") and uri in self.project_mappings:
            return self.project_mappings[uri]

        # 3. Wildcard Match (e.g., "skill:*" -> "git://...")
        # We iterate over mappings to find matching wildcards
        # Only Config currently supports wildcards as per typical use case, 
        # but we could extend to project mappings if needed.
        if hasattr(self, "mappings") and self.mappings:
            best_match = None
            longest_prefix = 0
    
            for pattern, target in self.mappings.items():
                if pattern.endswith("*"):
                    prefix = pattern[:-1]
                    if uri.startswith(prefix):
                        if len(prefix) > longest_prefix:
                            best_match = target
                            longest_prefix = len(prefix)
            
            if best_match:
                return best_match

        return uri

# Global Accessor
def get_context_manager() -> ContextManager:
    return ContextManager()

