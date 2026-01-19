"""
Hooks Loader

Loads declarative hooks from hooks.json files.
Hooks are registered with the HookManager at plugin load time.
"""

import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .hook import HookManager

logger = logging.getLogger(__name__)


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
    
    def execute(self, context: Dict[str, Any]) -> None:
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
            cmd = self._interpolate(self.params.get("cmd", self.params.get("command", "")), context)
            # Substitute ${KOR_PLUGIN_ROOT} with actual plugin root from context
            if "KOR_PLUGIN_ROOT" in context:
                cmd = cmd.replace("${KOR_PLUGIN_ROOT}", str(context["KOR_PLUGIN_ROOT"]))
            try:
                result = subprocess.run(
                    cmd, 
                    shell=True, 
                    capture_output=True, 
                    text=True,
                    timeout=self.params.get("timeout", 30),
                    env={**os.environ, "KOR_PLUGIN_ROOT": str(context.get("KOR_PLUGIN_ROOT", ""))}
                )
                if result.returncode != 0:
                    logger.warning(f"Hook command failed: {result.stderr}")
                else:
                    logger.debug(f"Hook command output: {result.stdout}")
            except subprocess.TimeoutExpired:
                logger.warning(f"Hook command timed out: {cmd}")
            except Exception as e:
                logger.error(f"Hook command error: {e}")
                
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
    
    def __init__(self, hook_manager: Optional["HookManager"] = None, plugin_root: Optional[Path] = None):
        """
        Initialize the HooksLoader.
        
        Args:
            hook_manager: Optional HookManager to register hooks with
            plugin_root: Plugin root directory for ${KOR_PLUGIN_ROOT} interpolation
        """
        self._hook_manager = hook_manager
        self._plugin_root = plugin_root
        self._loaded_actions: Dict[str, List[DeclarativeAction]] = {}
    
    def load_file(self, hooks_path: Path, plugin_root: Optional[Path] = None) -> Dict[str, List[DeclarativeAction]]:
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
    
    def _register_with_manager(self, hooks: Dict[str, List[DeclarativeAction]]) -> None:
        """Register loaded hooks with the HookManager."""
        from ..events.hook import HookEvent
        
        # Map string event names to HookEvent enum
        event_map = {e.value: e for e in HookEvent}
        
        for event_name, actions in hooks.items():
            hook_event = event_map.get(event_name)
            if not hook_event:
                logger.warning(f"Unknown hook event: {event_name}")
                continue
            
            # Create a callback that executes all actions
            def create_callback(action_list: List[DeclarativeAction]) -> Callable:
                def callback(*args, **kwargs) -> None:
                    context = dict(kwargs)
                    # Add positional args with generic names
                    for i, arg in enumerate(args):
                        context[f"arg{i}"] = arg
                    
                    for action in action_list:
                        try:
                            action.execute(context)
                        except Exception as e:
                            logger.error(f"Declarative hook action failed: {e}")
                return callback
            
            self._hook_manager.register(hook_event, create_callback(actions))
            logger.debug(f"Registered declarative hooks for {event_name}")
    
    def get_loaded_hooks(self) -> Dict[str, List[DeclarativeAction]]:
        """Get all loaded declarative hooks."""
        return self._loaded_actions
