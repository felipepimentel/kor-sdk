from typing import Type
from pydantic import BaseModel, Field
from .base import KorTool
import asyncio
import logging

logger = logging.getLogger(__name__)

class LSPParams(BaseModel):
    file_path: str = Field(..., description="Absolute path to the file.")
    line: int = Field(..., description="1-based line number.")
    character: int = Field(..., description="1-based character/column number.")

class LSPHoverTool(KorTool):
    name: str = "lsp_hover"
    description: str = "Get hover information (documentation/types) for a symbol at a specific file position."
    args_schema: Type[BaseModel] = LSPParams

    def _run(self, file_path: str, line: int, character: int) -> str:
        """Synchronous wrapper for async execution if needed via Loop."""
        # For LangChain tools, we should implement _arun ideally.
        # But if running in sync context, we bridge it.
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We are already in async loop (likely), so we should use _arun or specific async call
                # But BaseTool default run calls _run. 
                # If we are called from async agent, it calls _arun.
                return "Use _arun for LSP operations."
        except Exception:
            pass
        return asyncio.run(self._arun(file_path, line, character))

    async def _arun(self, file_path: str, line: int, character: int) -> str:
        from ..kernel import get_kernel
        kernel = get_kernel()
        manager = kernel.registry.get_service("lsp")
        
        if not manager:
            return "LSP Service not available."
            
        # 1. Detect Language / Get Client
        # We need to map file extension to language config name?
        # LSPManager currently takes language name.
        # Ideally Registry or Manager logic resolves name from path.
        # Let's fix Manager to resolve extension -> client first.
        
        # HACK: Iterate languages in manager to find match
        client = None
        for lang, config in manager.languages.items():
            ext = "." + file_path.split(".")[-1]
            if ext in config.extensions:
                client = await manager.get_client(lang)
                break
        
        if not client:
            return f"No LSP client configured for file: {file_path}"
            
        # 2. Send Request
        # Note: LSP uses 0-based indexing
        # Note: We need to open the document first if not open?
        # Ideally we send textDocument/didOpen first. 
        # But for stateless tool use, we can try relying on server reading from disk (most do).
        # Or we explicitly open it.
        
        uri = f"file://{file_path}"
        
        # Send didOpen to ensure server knows about it (Stateless safety)
        from pathlib import Path
        text = Path(file_path).read_text()
        
        await client.send_notification("textDocument/didOpen", {
            "textDocument": {
                "uri": uri,
                "languageId": lang, # e.g. "python"
                "version": 1,
                "text": text
            }
        })
        
        response = await client.send_request("textDocument/hover", {
            "textDocument": {"uri": uri},
            "position": {"line": line - 1, "character": character - 1}
        })
        
        if not response or not response.get("contents"):
            return "No hover information found."
            
        contents = response["contents"]
        # Normalize response
        if isinstance(contents, dict) and "value" in contents:
            return contents["value"]
        elif isinstance(contents, list):
            return "\n".join([str(c) for c in contents])
            
        return str(contents)

class LSPDefinitionTool(KorTool):
    name: str = "lsp_definition"
    description: str = "Go to definition of the symbol at the given position."
    args_schema: Type[BaseModel] = LSPParams

    def _run(self, file_path: str, line: int, character: int) -> str:
        return asyncio.run(self._arun(file_path, line, character))

    async def _arun(self, file_path: str, line: int, character: int) -> str:
        from ..kernel import get_kernel
        kernel = get_kernel()
        manager = kernel.registry.get_service("lsp")
        
        if not manager:
            return "LSP Service unavailable."

        client = None
        target_lang = "text"
        for lang, config in manager.languages.items():
            ext = "." + file_path.split(".")[-1]
            if ext in config.extensions:
                client = await manager.get_client(lang)
                target_lang = lang
                break
        
        if not client:
            return f"No LSP client for {file_path}"

        uri = f"file://{file_path}"
        try:
            # Ensure open
            text = open(file_path).read()
            await client.send_notification("textDocument/didOpen", {
                "textDocument": {
                    "uri": uri,
                    "languageId": target_lang,
                    "version": 1,
                    "text": text
                }
            })
            
            response = await client.send_request("textDocument/definition", {
                "textDocument": {"uri": uri},
                "position": {"line": line - 1, "character": character - 1}
            })
            
            if not response:
                return "No definition found."
                
            # Response can be Location or Location[]
            locs = response if isinstance(response, list) else [response]
            result = []
            for loc in locs:
                if "uri" in loc and "range" in loc:
                    f = loc["uri"].replace("file://", "")
                    line_num = loc["range"]["start"]["line"] + 1
                    result.append(f"{f}:{line_num}")
            
            return "\n".join(result)
            
        except Exception as e:
            return f"LSP Error: {e}"
