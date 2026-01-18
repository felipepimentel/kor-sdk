"""
Telemetry and Structured Logging for KOR.
"""
import json
import time
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from .hook import HookManager, HookEvent

logger = logging.getLogger(__name__)

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

def setup_telemetry(hooks: HookManager):
    """Initializes and registers the telemetry subscriber."""
    subscriber = TelemetrySubscriber()
    
    # Subscribe to all events
    hooks.register_global_listener(subscriber.on_event)
