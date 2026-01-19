from kor_core.plugin import KorPlugin, KorContext
from .tools import SystemInfoTool

class SystemInfoPlugin(KorPlugin):
    @property
    def id(self) -> str:
        return "kor-plugin-system-info"

    def initialize(self, context: KorContext) -> None:
        # Register the tool
        registry = context.registry.get_service("tools")
        if registry:
            registry.register_class(SystemInfoTool, tags=["system", "info", "os", "debug"])
