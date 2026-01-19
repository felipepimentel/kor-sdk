import logging
import json
from typing import Dict, Any
from .events.hook import TelemetrySink, HookEvent

logger = logging.getLogger(__name__)

class LoggingTelemetrySink(TelemetrySink):
    """
    A simple telemetry sink that logs events standard python logging.
    Useful for debugging or local analytics.
    """
    def __init__(self, level: int = logging.INFO):
        self.level = level

    def capture(self, event: HookEvent, data: Dict[str, Any]):
        # Filter out heavy objects if necessary, or just basic serialization
        safe_data = {
            k: str(v) for k, v in data.items() 
            if isinstance(v, (str, int, float, bool, type(None)))
        }
        
        msg = {
            "event": event.value,
            "data": safe_data
        }
        
        logger.log(self.level, f"Telemetry: {json.dumps(msg)}")
