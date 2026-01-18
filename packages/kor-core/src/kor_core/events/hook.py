from typing import Dict, List, Callable, Any
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class HookEvent(str, Enum):
    """
    Comprehensive hook events inspired by Claude Code.
    """
    # Lifecycle hooks
    ON_BOOT = "on_boot"
    ON_SHUTDOWN = "on_shutdown"
    
    # Command hooks
    PRE_COMMAND = "pre_command"
    POST_COMMAND = "post_command"
    
    # Agent hooks
    ON_AGENT_START = "on_agent_start"
    ON_AGENT_END = "on_agent_end"
    ON_AGENT_ERROR = "on_agent_error"
    
    # Node/Step hooks
    ON_NODE_START = "on_node_start"
    ON_NODE_END = "on_node_end"
    
    # Tool hooks
    ON_TOOL_CALL = "on_tool_call"
    AFTER_TOOL_CALL = "after_tool_call"
    ON_TOOL_ERROR = "on_tool_error"
    
    # Message hooks
    ON_USER_MESSAGE = "on_user_message"
    ON_ASSISTANT_MESSAGE = "on_assistant_message"
    
    # Context hooks
    ON_CONTEXT_CHANGE = "on_context_change"
    ON_FILE_READ = "on_file_read"
    ON_FILE_WRITE = "on_file_write"
    
    # Permission hooks
    ON_PERMISSION_REQUEST = "on_permission_request"
    ON_PERMISSION_GRANTED = "on_permission_granted"
    ON_PERMISSION_DENIED = "on_permission_denied"

class HookManager:
    """
    Event Bus for KOR.
    Plugins can register callbacks for specific lifecycle events.
    """
    def __init__(self):
        self._hooks: Dict[str, List[Callable]] = {e.value: [] for e in HookEvent}
        self._global_listeners: List[Callable] = []

    def register_global_listener(self, callback: Callable):
        """Register a callback that receives every emitted event."""
        self._global_listeners.append(callback)
        logger.debug("Registered global hook listener")

    def register(self, event: HookEvent, callback: Callable):
        """Register a function to be called on event."""
        if event.value not in self._hooks:
            self._hooks[event.value] = []
        self._hooks[event.value].append(callback)
        logger.debug(f"Registered hook for {event.value}")

    def on(self, event: HookEvent):
        """Decorator to register a hook callback."""
        def decorator(func: Callable):
            self.register(event, func)
            return func
        return decorator

    async def emit(self, event: HookEvent, *args, **kwargs):
        """Emit an event, awaiting all async listeners."""
        # 1. Global listeners
        for listener in self._global_listeners:
            try:
                if is_async_callable(listener):
                    await listener(event, *args, **kwargs)
                else:
                    listener(event, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in global hook listener {listener}: {e}")

        # 2. Specific listeners
        listeners = self._hooks.get(event.value, [])
        for listener in listeners:
            try:
                if is_async_callable(listener):
                    await listener(*args, **kwargs)
                else:
                    listener(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in hook listener {listener} for event {event.value}: {e}")

    def emit_sync(self, event: HookEvent, *args, **kwargs):
        """Synchronous emit for non-async contexts."""
        # 1. Global listeners
        for listener in self._global_listeners:
            try:
                if not is_async_callable(listener):
                    listener(event, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in global hook listener {listener}: {e}")

        # 2. Specific listeners
        listeners = self._hooks.get(event.value, [])
        for listener in listeners:
            try:
                if not is_async_callable(listener):
                    listener(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in hook listener {listener} for event {event.value}: {e}")

def is_async_callable(obj: Any) -> bool:
    import inspect
    return inspect.iscoroutinefunction(obj)
