from kor_core.plugin import KorPlugin, KorContext
from .provider import LiteLLMProvider

class LiteLLMPlugin(KorPlugin):
    """
    LiteLLM Provider Plugin for KOR.
    """
    
    @property
    def id(self) -> str:
        return "kor-llm-litellm"

    @property
    def provides(self) -> list[str]:
        return ["llm-provider-litellm"]

    def initialize(self, context: KorContext) -> None:
        """Registers the LiteLLM Provider with the LLM Registry."""
        try:
            llm_registry = context.registry.get_service("llm")
            llm_registry.register(LiteLLMProvider())
        except KeyError:
            pass

__all__ = ["LiteLLMPlugin"]
