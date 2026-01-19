"""
Bridge between OpenAI API format and KOR SDK Agent.
"""

import json
import logging
from typing import AsyncGenerator, List, Dict, Any
from kor_core import GraphRunner
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from ..schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChunk,
    Choice,
    ChoiceDelta,
    DeltaMessage,
    Message,
    Usage,
)

logger = logging.getLogger(__name__)


class OpenAIToKORAdapter:
    """Adapts OpenAI requests to KOR GraphRunner and vice versa."""

    def __init__(self):
        # We need to boot the kernel to get the registry and config
        from kor_core.kernel import get_kernel
        self.kernel = get_kernel()
        try:
            self.kernel.boot_sync()
            active_id = self.kernel.config.agent.active_graph
            agent_registry = self.kernel.registry.get_service("agents")
            self.graph = agent_registry.load_graph(active_id)
            self.runner = GraphRunner(graph=self.graph)
        except Exception as e:
            logger.error(f"Failed to initialize agent graph: {e}")
            # Fallback to default if boot/load fails
            self.runner = GraphRunner()

    async def run_chat(self, request: ChatCompletionRequest) -> AsyncGenerator[ChatCompletionChunk, None]:
        """Runs the agent and yields OpenAI-compatible chunks."""
        
        # 1. Extract inputs
        # Currently KOR GraphRunner takes a single string. 
        # We take the last user message as the primary query.
        last_user_msg = next((m.content for m in reversed(request.messages) if m.role == "user"), "")
        
        # 2. Run the Graph
        # Note: GraphRunner.run yields dictionaries representing LangGraph events.
        # Example event: {"Coder": {"messages": [AIMessage(...)]}}
        
        chunk_id = f"chatcmpl-{json.dumps(request.model_dump())[:10]}" # Stable-ish ID
        
        try:
            # We wrap the synchronous runner in an async context if needed, 
            # but usually LangGraph stream is sync-generator based unless configured otherwise.
            # For simplicity, we assume GraphRunner.run is sync.
            for event in self.runner.run(last_user_msg):
                for node, details in event.items():
                    # Handle message outputs from workers
                    if node in ["Coder", "Researcher"]:
                        messages = details.get("messages", [])
                        for msg in messages:
                            content = getattr(msg, "content", "")
                            if content:
                                yield ChatCompletionChunk(
                                    model=request.model,
                                    choices=[
                                        ChoiceDelta(
                                            index=0,
                                            delta=DeltaMessage(content=content)
                                        )
                                    ]
                                )
                    
                    # You could also emit "Thinking..." steps or node transitions here
                    # as OpenAI comments or hidden tokens, but for now we follow the spec.
            
            # Final chunk to signal completion
            yield ChatCompletionChunk(
                model=request.model,
                choices=[
                    ChoiceDelta(
                        index=0,
                        delta=DeltaMessage(),
                        finish_reason="stop"
                    )
                ]
            )

        except Exception as e:
            logger.error(f"Error in adapter run: {e}")
            yield ChatCompletionChunk(
                model=request.model,
                choices=[
                    ChoiceDelta(
                        index=0,
                        delta=DeltaMessage(content=f"\nError: {str(e)}"),
                        finish_reason="stop"
                    )
                ]
            )

    async def run_chat_sync(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Runs the agent and returns a full OpenAI-compatible response."""
        
        last_user_msg = next((m.content for m in reversed(request.messages) if m.role == "user"), "")
        full_content = []
        
        try:
            for event in self.runner.run(last_user_msg):
                for node, details in event.items():
                    if node in ["Coder", "Researcher"]:
                        messages = details.get("messages", [])
                        for msg in messages:
                            content = getattr(msg, "content", "")
                            if content:
                                full_content.append(content)
            
            content_str = "\n".join(full_content)
            
            return ChatCompletionResponse(
                model=request.model,
                choices=[
                    Choice(
                        index=0,
                        message=Message(role="assistant", content=content_str),
                        finish_reason="stop"
                    )
                ],
                usage=Usage(
                    prompt_tokens=0,  # TODO: Implement token counting
                    completion_tokens=0,
                    total_tokens=0
                )
            )

        except Exception as e:
            logger.error(f"Error in adapter run sync: {e}")
            return ChatCompletionResponse(
                model=request.model,
                choices=[
                    Choice(
                        index=0,
                        message=Message(role="assistant", content=f"Error: {str(e)}"),
                        finish_reason="stop"
                    )
                ]
            )
