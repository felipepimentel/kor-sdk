"""
DEPRECATED: This module is kept for backward compatibility with apps/tui.
For new code, use `kor_core.events.HookManager` and `kor_core.events.HookEvent` instead.
"""
import warnings
warnings.warn(
    "kor_core.events is deprecated. Use kor_core.events.hook instead.",
    DeprecationWarning,
    stacklevel=2
)

from typing import Protocol, Any, Dict
from enum import Enum
from pydantic import BaseModel

class EventType(str, Enum):
    AGENT_THINKING = "agent.thinking"
    TOOL_CALL_STARTED = "tool.started"
    TOOL_CALL_JX_kvENDED = "tool.ended"
    CONTEXT_UPDATED = "context.updated"
    APPROVAL_REQUESTED = "approval.requested"

class KorEvent(BaseModel):
    type: EventType
    payload: Dict[str, Any]

class KorEventListener(Protocol):
    async def on_event(self, event: KorEvent) -> None:
        """Handle an incoming event from the core."""
        ...

class EventBus:
    def __init__(self):
        self._listeners: list[KorEventListener] = []

    def subscribe(self, listener: KorEventListener):
        self._listeners.append(listener)

    async def emit(self, event: KorEvent):
        for listener in self._listeners:
            await listener.on_event(event)

    async def publish(self, type: EventType, payload: Dict[str, Any]):
        event = KorEvent(type=type, payload=payload)
        await self.emit(event)
