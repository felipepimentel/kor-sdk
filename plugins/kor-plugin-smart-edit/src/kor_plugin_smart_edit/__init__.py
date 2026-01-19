from kor_core.plugin import KorPlugin, KorContext
from .tools import SmartEditTool

class SmartEditPlugin(KorPlugin):
    @property
    def id(self) -> str:
        return "kor-plugin-smart-edit"

    def initialize(self, context: KorContext) -> None:
        registry = context.registry.get_service("tools")
        if registry:
            registry.register_class(SmartEditTool, tags=["editing", "code", "safe"])
