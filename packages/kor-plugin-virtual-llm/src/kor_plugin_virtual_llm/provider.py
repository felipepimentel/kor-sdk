from typing import Any, Dict, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration

from kor_core.llm.provider import BaseLLMProvider
import logging

logger = logging.getLogger(__name__)

class ProgrammableChatModel(BaseChatModel):
    """
    A mock chat model that returns responses based on configured rules.
    Supports:
    - Fixed response (default)
    - Sequence of responses (pop from list)
    - Trigger-based responses (if input contains X, return Y)
    """
    response_text: str = "Virtual Response"
    queue: List[str] = []
    triggers: Dict[str, str] = {}
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        last_msg = messages[-1].content if messages else ""
        logger.info(f"Virtual Model Input: {last_msg[:50]}...")
        
        # 1. Check Triggers
        for trigger, response in self.triggers.items():
            if trigger in str(last_msg):
                logger.info(f"Trigger matched: '{trigger}'")
                return self._create_result(response)
        
        # 2. Check Queue
        if self.queue:
            resp = self.queue.pop(0)
            logger.info("Popped response from queue")
            return self._create_result(resp)
            
        # 3. Default
        return self._create_result(self.response_text)

    def _create_result(self, text: str) -> ChatResult:
        # Check if text looks like a tool call (formatted for LangChain usually, 
        # but for simplicity we assume the agent accepts raw text or we mock the message structure)
        # Note: In a real advanced mock we might return AIMessage with tool_calls set.
        # For now, we return text.
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])

    @property
    def _llm_type(self) -> str:
        return "virtual-programmable"

class VirtualProvider(BaseLLMProvider):
    """Provider for Virtual LLM."""
    
    def __init__(self, name: str = "virtual"):
        self.name = name

    def get_chat_model(
        self, 
        model_name: str, 
        config: Dict[str, Any]
    ):
        defaults = config.get("default_response", "Virtual Response")
        queue = config.get("queue", [])
        triggers = config.get("triggers", {})
        
        return ProgrammableChatModel(
            response_text=defaults,
            queue=queue,
            triggers=triggers
        )

    def validate_config(self, config: Dict[str, Any]) -> bool:
        return True
