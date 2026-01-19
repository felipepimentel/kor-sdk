import asyncio
import json
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class AsyncLSPClient:
    """
    A low-level async JSON-RPC 2.0 client for communicating with Language Servers via stdio.
    """
    def __init__(self, command: str, args: list[str], cwd: Optional[str] = None):
        self.command = command
        self.args = args
        self.cwd = cwd or os.getcwd()
        self.process: Optional[asyncio.subprocess.Process] = None
        self._request_id = 0
        self._pending_requests: Dict[int, asyncio.Future] = {}
        self._read_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Starts the Language Server process."""
        try:
            self.process = await asyncio.create_subprocess_exec(
                self.command, *self.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.cwd
            )
            # Start reading loop
            self._read_task = asyncio.create_task(self._read_loop())
            logger.info(f"LSP Client started: {self.command} {self.args}")
        except Exception as e:
            logger.error(f"Failed to start LSP client: {e}")
            raise

    async def stop(self):
        """Stops the Language Server process."""
        if self.process:
            try:
                self.process.terminate()
                await self.process.wait()
            except Exception as e:
                logger.error(f"Error stopping LSP client: {e}")
            finally:
                if self._read_task:
                    self._read_task.cancel()
                self.process = None

    async def send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Sends a JSON-RPC request and waits for the response."""
        if not self.process:
            raise RuntimeError("LSP Client is not running.")

        self._request_id += 1
        request_id = self._request_id
        
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }
        
        future = asyncio.Future()
        self._pending_requests[request_id] = future
        
        await self._write_message(payload)
        
        try:
            # Wait for response with timeout?
            return await future
        except Exception as e:
            del self._pending_requests[request_id]
            raise e

    async def send_notification(self, method: str, params: Optional[Dict[str, Any]] = None):
        """Sends a JSON-RPC notification (no response expected)."""
        if not self.process:
            raise RuntimeError("LSP Client is not running.")
            
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        await self._write_message(payload)

    async def _write_message(self, payload: Dict[str, Any]):
        """Writes a JSON-RPC message with Content-Length header."""
        body = json.dumps(payload).encode('utf-8')
        header = f"Content-Length: {len(body)}\r\n\r\n".encode('ascii')
        
        if self.process and self.process.stdin:
            self.process.stdin.write(header + body)
            await self.process.stdin.drain()

    async def _read_loop(self):
        """Continuously reads messages from stdout."""
        try:
            while self.process and self.process.stdout:
                # 1. Read Headers
                # Headers are terminated by \r\n\r\n
                header_line = await self.process.stdout.readline()
                if not header_line:
                    break # EOF
                
                content_length = 0
                while header_line != b'\r\n':
                    decoded = header_line.decode('ascii').strip()
                    if decoded.startswith("Content-Length:"):
                        content_length = int(decoded.split(":", 1)[1].strip())
                    header_line = await self.process.stdout.readline()

                # 2. Read Body
                if content_length > 0:
                    body = await self.process.stdout.readexactly(content_length)
                    message = json.loads(body)
                    self._handle_message(message)
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"LSP Read Error: {e}")

    def _handle_message(self, message: Dict[str, Any]):
        """Dispatches incoming messages."""
        if "id" in message and message["id"] in self._pending_requests:
            # Response to a request
            future = self._pending_requests.pop(message["id"])
            if "error" in message:
                future.set_exception(RuntimeError(f"LSP Error: {message['error']}"))
            else:
                future.set_result(message.get("result"))
        else:
            # Notification or Request from Server (not handled yet)
            logger.debug(f"Received notification: {message}")
