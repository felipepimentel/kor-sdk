from kor_core.plugin import KorPlugin, KorContext
from .provider import OpenAIProvider

class OpenAIPlugin(KorPlugin):
    """
    Standard OpenAI Provider Plugin for KOR.
    """
    
    @property
    def id(self) -> str:
        return "kor-llm-openai"

    @property
    def provides(self) -> list[str]:
        return ["llm-provider-openai"]

    def initialize(self, context: KorContext) -> None:
        """Registers the OpenAI Provider with the LLM Registry."""
        try:
            llm_registry = context.registry.get_service("llm")
            llm_registry.register(OpenAIProvider())
        except KeyError:
            # Fallback if LLM service isn't registered (shouldn't happen in standard kernel boot)
            import logging
            logging.getLogger(__name__).warning("LLM Registry service not found. OpenAI provider NOT registered.")

__all__ = ["OpenAIPlugin"]
