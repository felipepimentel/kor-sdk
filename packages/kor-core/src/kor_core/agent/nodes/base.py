from ...kernel import get_kernel
from ...tools.terminal import TerminalTool
from ...tools.browser import BrowserTool
import logging

logger = logging.getLogger(__name__)
def get_tool_from_registry(name: str):
    """Attempt to get a tool from the global registry, fallback to defaults."""
    try:
        k = get_kernel()
        registry = k.registry.get_service("tools")
        if registry:
            tool_info = registry.get(name)
            if tool_info:
                tool = tool_info.tool_class()
                if hasattr(tool, "registry"):
                    tool.registry = registry
                return tool
    except Exception as e:
        logger.warning(f"Failed to load tool '{name}' from registry: {e}")
    
    # Fallbacks for built-in tools if registry is missing
    if name == "terminal":
        return TerminalTool()
    if name == "browser":
        return BrowserTool()
    return None
