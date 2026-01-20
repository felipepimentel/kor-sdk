"""
Unified Events System for KOR SDK

Provides:
- HookEvent enum: All lifecycle events
- HookManager: Event bus for registering and emitting events
- DeclarativeAction: Actions that can be triggered from hooks.json
- HooksLoader: Load declarative hooks from JSON files
- TelemetrySubscriber: JSONL telemetry logging
"""

import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol

logger = logging.getLogger(__name__)


# =============================================================================
# Hook Events
# =============================================================================

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
    
    # Planning hooks (Phase 3)
    PLAN_UPDATED = "plan_updated"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    PLAN_FINISHED = "plan_finished"  # All tasks complete


# =============================================================================
# Telemetry
# =============================================================================

class TelemetrySink(Protocol):
    """Protocol for telemetry sinks."""
    def capture(self, event: HookEvent, data: Dict[str, Any]):
        ...


class TelemetrySubscriber:
    """
    Subscribes to HookManager events and writes telemetry to a JSONL file.
    """
    def __init__(self, log_path: Optional[str] = None):
        if not log_path:
            home = Path.home()
            log_dir = home / ".kor" / "telemetry"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = str(log_dir / "trace.jsonl")
            
        self.log_path = log_path

    def on_event(self, event: HookEvent, *args, **kwargs):
        """Processes a hook event and logs it."""
        # Clean data for JSON serialization
        clean_kwargs = {}
        for k, v in kwargs.items():
            if isinstance(v, (str, int, float, bool, type(None), dict, list)):
                clean_kwargs[k] = v
            else:
                clean_kwargs[k] = str(v)

        entry = {
            "timestamp": time.time(),
            "event": event.value,
            "data": clean_kwargs
        }
        
        try:
            with open(self.log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write telemetry: {e}")


def setup_telemetry(hooks: "HookManager"):
    """Initializes and registers the telemetry subscriber."""
    subscriber = TelemetrySubscriber()
    hooks.register_global_listener(subscriber.on_event)


class LoggingTelemetrySink(TelemetrySink):
    """
    A simple telemetry sink that logs events via standard Python logging.
    Useful for debugging or local analytics.
    
    Example:
        hooks = HookManager()
        hooks.register_telemetry_sink(LoggingTelemetrySink(level=logging.DEBUG))
    """
    def __init__(self, level: int = logging.INFO):
        self.level = level

    def capture(self, event: HookEvent, data: Dict[str, Any]):
        import json as _json
        # Filter out heavy objects if necessary
        safe_data = {
            k: str(v) for k, v in data.items() 
            if isinstance(v, (str, int, float, bool, type(None)))
        }
        
        msg = {
            "event": event.value,
            "data": safe_data
        }
        
        logger.log(self.level, f"Telemetry: {_json.dumps(msg)}")


# =============================================================================
# Hook Manager
# =============================================================================

def is_async_callable(obj: Any) -> bool:
    import inspect
    return inspect.iscoroutinefunction(obj)


class HookManager:
    """
    Event Bus for KOR.
    Plugins can register callbacks for specific lifecycle events.
    """
    def __init__(self):
        self._hooks: Dict[str, List[Callable]] = {e.value: [] for e in HookEvent}
        self._global_listeners: List[Callable] = []
        self._telemetry_sinks: List[TelemetrySink] = []

    def register_global_listener(self, callback: Callable):
        """Register a callback that receives every emitted event."""
        self._global_listeners.append(callback)
        logger.debug("Registered global hook listener")

    def register_telemetry_sink(self, sink: TelemetrySink):
        """Register a telemetry sink."""
        self._telemetry_sinks.append(sink)
        logger.info(f"Registered telemetry sink: {sink}")

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
        data = kwargs  # Capture kwargs as data context for telemetry
        
        # 1. Telemetry Sinks (Fire and Forget / Safe)
        for sink in self._telemetry_sinks:
            try:
                sink.capture(event, data)
            except Exception as e:
                logger.warning(f"Telemetry sink failed: {e}")

        # 2. Global listeners
        for listener in self._global_listeners:
            try:
                if is_async_callable(listener):
                    await listener(event, *args, **kwargs)
                else:
                    listener(event, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in global hook listener {listener}: {e}")

        # 3. Specific listeners
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
        data = kwargs

        # 1. Telemetry Sinks
        for sink in self._telemetry_sinks:
            try:
                sink.capture(event, data)
            except Exception as e:
                logger.warning(f"Telemetry sink failed: {e}")

        # 2. Global listeners
        for listener in self._global_listeners:
            try:
                if not is_async_callable(listener):
                    listener(event, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in global hook listener {listener}: {e}")

        # 3. Specific listeners
        listeners = self._hooks.get(event.value, [])
        for listener in listeners:
            try:
                if not is_async_callable(listener):
                    listener(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in hook listener {listener} for event {event.value}: {e}")


# =============================================================================
# Declarative Hooks (JSON-based)
# =============================================================================

@dataclass
class DeclarativeAction:
    """
    A single action to execute when a hook is triggered.
    
    Supported action types:
    - log: Log a message (supports {variable} interpolation)
    - emit_metric: Emit a metric event
    - command: Run a shell command
    - set_context: Set a context variable
    """
    action_type: str
    params: Dict[str, Any] = field(default_factory=dict)
    
    async def execute(self, context: Dict[str, Any]) -> None:
        """
        Execute the action with the given context.
        
        Args:
            context: Dictionary of context variables for interpolation
        """
        if self.action_type == "log":
            message = self._interpolate(self.params.get("message", ""), context)
            level = self.params.get("level", "info").lower()
            getattr(logger, level, logger.info)(message)
            
        elif self.action_type == "emit_metric":
            # Placeholder for metric emission
            name = self.params.get("name", "unknown")
            value = self.params.get("value", 1)
            logger.debug(f"Metric: {name}={value}")
            
        elif self.action_type == "command":
            cmd = self._interpolate(
                self.params.get("cmd", self.params.get("command", "")), 
                context
            )
            # Substitute ${KOR_PLUGIN_ROOT} with actual plugin root from context
            if "KOR_PLUGIN_ROOT" in context:
                cmd = cmd.replace("${KOR_PLUGIN_ROOT}", str(context["KOR_PLUGIN_ROOT"]))
                
            try:
                # Use Kernel Sandbox for execution!
                # This ensures we respect security policies (Docker, etc.)
                from .kernel import get_kernel
                kernel = get_kernel()
                
                # We reuse the sandbox. run_command usually returns stdout 
                # or raises exception on failure.
                # Note: run_command signature is now async
                output = await kernel.sandbox.run_command(cmd)
                logger.debug(f"Hook command output: {output}")
                
            except Exception as e:
                logger.error(f"Hook command failed: {e}")
                
        elif self.action_type == "set_context":
            key = self.params.get("key")
            value = self._interpolate(str(self.params.get("value", "")), context)
            if key:
                context[key] = value
    
    def _interpolate(self, template: str, context: Dict[str, Any]) -> str:
        """Interpolate {variables} in the template string."""
        try:
            return template.format(**context)
        except KeyError:
            # Return template with missing keys unchanged
            return template


class HooksLoader:
    """
    Loads declarative hooks from hooks.json files.
    
    Supports Claude Code-style format with script execution:
    ```json
    {
      "hooks": {
        "on_boot": [{
          "type": "command",
          "command": "python3 ${KOR_PLUGIN_ROOT}/hooks/on_boot.py",
          "timeout": 10
        }]
      }
    }
    ```
    
    Also supports simplified KOR format:
    ```json
    {
      "on_agent_start": [
        {"log": {"message": "Agent {agent_id} starting...", "level": "info"}},
        {"command": {"cmd": "echo 'Tool: {tool_name}'"}}
      ]
    }
    ```
    """
    
    def __init__(
        self, 
        hook_manager: Optional[HookManager] = None, 
        plugin_root: Optional[Path] = None
    ):
        """
        Initialize the HooksLoader.
        
        Args:
            hook_manager: Optional HookManager to register hooks with
            plugin_root: Plugin root directory for ${KOR_PLUGIN_ROOT} interpolation
        """
        self._hook_manager = hook_manager
        self._plugin_root = plugin_root
        self._loaded_actions: Dict[str, List[DeclarativeAction]] = {}
    
    def load_file(
        self, 
        hooks_path: Path, 
        plugin_root: Optional[Path] = None
    ) -> Dict[str, List[DeclarativeAction]]:
        """
        Load hooks from a hooks.json file.
        
        Args:
            hooks_path: Path to the hooks.json file
            plugin_root: Optional plugin root for variable interpolation
            
        Returns:
            Dictionary mapping event names to lists of actions
        """
        # Use provided plugin_root or infer from hooks_path
        root = plugin_root or self._plugin_root or hooks_path.parent
        self._current_plugin_root = root
        
        if not hooks_path.exists():
            logger.debug(f"Hooks file does not exist: {hooks_path}")
            return {}
        
        try:
            with open(hooks_path, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in hooks file {hooks_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load hooks file {hooks_path}: {e}")
            return {}
        
        loaded = {}
        
        for event_name, actions_data in data.items():
            if not isinstance(actions_data, list):
                actions_data = [actions_data]
            
            actions = []
            for action_data in actions_data:
                action = self._parse_action(action_data)
                if action:
                    actions.append(action)
            
            if actions:
                loaded[event_name] = actions
                logger.info(f"Loaded {len(actions)} declarative actions for {event_name}")
        
        self._loaded_actions.update(loaded)
        
        # Register with HookManager if provided
        if self._hook_manager:
            self._register_with_manager(loaded)
        
        return loaded
    
    def _parse_action(self, action_data: Dict[str, Any]) -> Optional[DeclarativeAction]:
        """Parse a single action from JSON data."""
        # Support shorthand: {"log": "message"} -> {"log": {"message": "message"}}
        for action_type in ["log", "emit_metric", "command", "set_context"]:
            if action_type in action_data:
                params = action_data[action_type]
                if isinstance(params, str):
                    # Shorthand
                    if action_type == "log":
                        params = {"message": params}
                    elif action_type == "command":
                        params = {"cmd": params}
                    else:
                        params = {"value": params}
                
                return DeclarativeAction(action_type=action_type, params=params)
        
        logger.warning(f"Unknown action format: {action_data}")
        return None
    
    def _register_with_manager(
        self, 
        hooks: Dict[str, List[DeclarativeAction]]
    ) -> None:
        """Register loaded hooks with the HookManager."""
        # Map string event names to HookEvent enum
        event_map = {e.value: e for e in HookEvent}
        
        for event_name, actions in hooks.items():
            hook_event = event_map.get(event_name)
            if not hook_event:
                logger.warning(f"Unknown hook event: {event_name}")
                continue
            
            # Create a callback that executes all actions
            def create_callback(action_list: List[DeclarativeAction]) -> Callable:
                async def callback(*args, **kwargs) -> None:
                    context = dict(kwargs)
                    # Add positional args with generic names
                    for i, arg in enumerate(args):
                        context[f"arg{i}"] = arg
                    
                    for action in action_list:
                        try:
                            await action.execute(context)
                        except Exception as e:
                            logger.error(f"Declarative hook action failed: {e}")
                return callback
            
            self._hook_manager.register(hook_event, create_callback(actions))
            logger.debug(f"Registered declarative hooks for {event_name}")
    
    def get_loaded_hooks(self) -> Dict[str, List[DeclarativeAction]]:
        """Get all loaded declarative hooks."""
        return self._loaded_actions
