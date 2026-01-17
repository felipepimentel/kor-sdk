from typing import Dict, List, Callable, Any
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class HookEvent(str, Enum):
    ON_BOOT = "on_boot"
    PRE_COMMAND = "pre_command"
    POST_COMMAND = "post_command"
    ON_SHUTDOWN = "on_shutdown"

class HookManager:
    """
    Event Bus for KOR.
    Plugins can register callbacks for specific lifecycle events.
    """
    def __init__(self):
        self._hooks: Dict[str, List[Callable]] = {e.value: [] for e in HookEvent}

    def register(self, event: HookEvent, callback: Callable):
        """Register a function to be called on event."""
        if event.value not in self._hooks:
            self._hooks[event.value] = []
        self._hooks[event.value].append(callback)
        logger.debug(f"Registered hook for {event.value}")

    async def emit(self, event: HookEvent, *args, **kwargs):
        """Emit an event, awaiting all async listeners."""
        listeners = self._hooks.get(event.value, [])
        for listener in listeners:
            try:
                # Naive check for async - in prod use inspect
                if is_async_callable(listener):
                    await listener(*args, **kwargs)
                else:
                    listener(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in hook listener {listener} for event {event.value}: {e}")

def is_async_callable(obj: Any) -> bool:
    import inspect
    return inspect.iscoroutinefunction(obj)
