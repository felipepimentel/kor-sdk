from ...kernel import get_kernel
from ...tools.terminal import TerminalTool
from ...tools.browser import BrowserTool

def get_tool_from_registry(name: str):
    """Attempt to get a tool from the global registry, fallback to defaults."""
    try:
        k = get_kernel()
        # Ensure kernel is booted if we are in a node
        # (Kernel.boot() is now async, so we might need to be careful if this is called from sync)
        # However, nodes are usually called within an async graph.
        
        registry = k.registry.get_service("tools")
        if registry:
            tool_info = registry.get(name)
            if tool_info:
                tool = tool_info.tool_class()
                if hasattr(tool, "registry"):
                    tool.registry = registry
                return tool
    except Exception:
        pass
    
    # Fallbacks for built-in tools if registry is missing
    if name == "terminal":
        return TerminalTool()
    if name == "browser":
        return BrowserTool()
    return None
