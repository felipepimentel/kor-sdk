"""
Registry for discovered agents.
"""

from typing import Dict, Optional, Any, List
from .models import AgentDefinition
from ..search import SearchableRegistry
import importlib
import logging

logger = logging.getLogger(__name__)

class AgentRegistry(SearchableRegistry[AgentDefinition]):
    """
    Stores validation definitions of available agents.
    Does NOT instantiate the graph until requested.
    """
    def __init__(self, backend: str = "regex"):
        super().__init__(backend)

    def register(self, agent: AgentDefinition, tags: Optional[List[str]] = None):
        if agent.id in self._items:
            logger.warning(f"Overwriting agent definition for {agent.id}")
        
        # Use ID as the key for AgentRegistry
        self._items[agent.id] = agent
        self._indexed = False
        logger.debug(f"Registered agent: {agent.id}")

    def list_agents(self) -> Dict[str, AgentDefinition]:
        """Returns the dictionary of registered agents."""
        return self._items
        
    def get_agent(self, agent_id: str) -> Optional[AgentDefinition]:
        return self.get(agent_id)

    def load_graph(self, agent_id: str) -> Any:
        """Loads and compiles the graph for the given agent."""
        if agent_id not in self._items:
            raise KeyError(f"Agent '{agent_id}' not found.")
        
        definition = self._items[agent_id]
        try:
            module_name, func_name = definition.entry.split(":")
            module = importlib.import_module(module_name)
            factory = getattr(module, func_name)
            return factory()
        except Exception as e:
            logger.error(f"Failed to load agent graph {agent_id}: {e}")
            raise

