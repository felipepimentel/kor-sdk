from typing import Dict, Optional
from .client import AsyncLSPClient
from ..config import LanguageConfig
import logging

logger = logging.getLogger(__name__)

class LSPManager:
    """
    Manages the lifecycle of multiple Language Servers (one per language).
    """
    def __init__(self, languages: Dict[str, LanguageConfig]):
        self.languages = languages
        self._clients: Dict[str, AsyncLSPClient] = {}

    async def get_client(self, lang_name: str) -> Optional[AsyncLSPClient]:
        """Gets or starts a client for the given language."""
        if lang_name not in self.languages:
            return None
            
        config = self.languages[lang_name]
        
        # Check if LSP is configured for this language via 'lsp' attribute
        lsp_config = getattr(config, "lsp", None)
        if not lsp_config:
            return None

        if lang_name in self._clients:
            return self._clients[lang_name]
            
        # Start new client
        client = AsyncLSPClient(lsp_config.command, lsp_config.args)
        await client.start()
        
        # Initialize (Required by LSP Spec)
        # textDocument/initialize ...
        # For now, we return the raw client. The TOOL should likely handle initialization 
        # or we do it here. Doing it here ensures it's ready.
        try:
            await client.send_request("initialize", {
                "processId": None,
                "rootUri": None, # Should be workspace root
                "capabilities": {}
            })
            await client.send_notification("initialized", {})
            self._clients[lang_name] = client
            return client
        except Exception as e:
            logger.error(f"Failed to initialize LSP for {lang_name}: {e}")
            await client.stop()
            return None

    async def stop_all(self):
        """Stops all running clients."""
        for client in self._clients.values():
            await client.stop()
        self._clients.clear()
