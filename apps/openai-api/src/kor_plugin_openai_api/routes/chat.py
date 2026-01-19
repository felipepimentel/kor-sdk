"""
Chat completion routes.
"""

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from ..schemas.chat import ChatCompletionRequest
from ..adapters.agent_adapter import OpenAIToKORAdapter

router = APIRouter()
adapter = OpenAIToKORAdapter()

@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completions endpoint.
    Supports both streaming and non-streaming requests.
    """
    
    if request.stream:
        async def event_generator():
            async for chunk in adapter.run_chat(request):
                # OpenAI format expects 'data: ' prefix and double newline
                # sse-starlette handles the formatting, we just yield the data
                yield {
                    "event": "message",
                    "data": chunk.model_dump_json()
                }
            yield {"event": "message", "data": "[DONE]"}

        return EventSourceResponse(event_generator())
    
    else:
        # Non-streaming request
        response = await adapter.run_chat_sync(request)
        return response
