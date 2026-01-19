"""
Registry for discovered agents.
"""

from typing import Dict, Optional, Any
from ..plugin.manifest import AgentDefinition
import importlib
import logging

logger = logging.getLogger(__name__)

class AgentRegistry:
    """
    Stores validation definitions of available agents.
    Does NOT instantiate the graph until requested.
    """
    def __init__(self):
        self._agents: Dict[str, AgentDefinition] = {}

    def register(self, agent: AgentDefinition):
        if agent.id in self._agents:
            logger.warning(f"Overwriting agent definition for {agent.id}")
        self._agents[agent.id] = agent
        logger.debug(f"Registered agent: {agent.id}")

    def list_agents(self) -> Dict[str, AgentDefinition]:
        return self._agents

    def get_agent(self, agent_id: str) -> Optional[AgentDefinition]:
        return self._agents.get(agent_id)

    def get(self, agent_id: str) -> Optional[AgentDefinition]:
        """Alias for get_agent."""
        return self.get_agent(agent_id)

    def load_graph(self, agent_id: str) -> Any:
        """Loads and compiles the graph for the given agent."""
        if agent_id not in self._agents:
            raise KeyError(f"Agent '{agent_id}' not found.")
        
        definition = self._agents[agent_id]
        try:
            module_name, func_name = definition.entry.split(":")
            module = importlib.import_module(module_name)
            factory = getattr(module, func_name)
            return factory()
        except Exception as e:
            logger.error(f"Failed to load agent graph {agent_id}: {e}")
            raise

