from typing import Type
from pydantic import BaseModel, Field
from .base import KorTool

# Optional dependency
try:
    from duckduckgo_search import DDGS
    HAS_DDG = True
except ImportError:
    HAS_DDG = False

class BrowserInput(BaseModel):
    query: str = Field(description="Search query")

class BrowserTool(KorTool):
    name: str = "browser"
    description: str = "Searches the web for information."
    args_schema: Type[BaseModel] = BrowserInput

    def _run(self, query: str) -> str:
        if not HAS_DDG:
            return "Error: duckduckgo-search not installed. Please install it to use this tool."
        
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
            return str(results)
        except Exception as e:
            return f"Error searching web: {e}"
