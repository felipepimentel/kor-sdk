import platform
import sys
from kor_core.tools import KorTool

class SystemInfoTool(KorTool):
    name: str = "system_info"
    description: str = "Returns information about the running system (OS, Python version)."
    
    def _run(self, query: str = "") -> str:
        return f"OS: {platform.system()} {platform.release()}\nPython: {sys.version}"
