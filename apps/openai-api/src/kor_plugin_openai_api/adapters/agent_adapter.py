"""
Bridge between OpenAI API format and KOR SDK Agent.
"""

import logging
from typing import AsyncGenerator, List
from kor_core import GraphRunner
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

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
        self.kernel = None
        self.graph = None
        self.runner = None
        
    def _ensure_initialized(self):
        """Lazily initialize the kernel and graph."""
        if self.runner:
            return
            
        try:
            # We need to boot the kernel to get the registry and config
            from kor_core.kernel import get_kernel
            from kor_core.agent.graph import create_graph
            
            self.kernel = get_kernel()
            self.kernel.boot_sync()
            
            active_id = self.kernel.config.agent.active_graph
            agent_registry = self.kernel.registry.get_service("agents")
            
            # Check if it's the internal supervisor or an external graph
            if active_id == "default-supervisor":
                # Ensure checkingpointer is available
                checkpointer = self.kernel.registry.get_service("checkpointer") if self.kernel.registry.has_service("checkpointer") else None
                self.graph = create_graph(checkpointer=checkpointer)
            else:
                 self.graph = agent_registry.load_graph(active_id)

            self.runner = GraphRunner(graph=self.graph)
            logger.info(f"Initialized OpenAIToKORAdapter with agent: {active_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent graph: {e}")
            # Fallback to empty runner if boot/load fails
            self.runner = GraphRunner()

    def _convert_messages(self, messages: List[Message]) -> List[BaseMessage]:
        """Converts OpenAI Pydantic messages to LangChain messages."""
        from langchain_core.messages import ToolMessage
        lc_messages = []
        for msg in messages:
            if msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content or ""))
            elif msg.role == "assistant":
                lc_messages.append(AIMessage(content=msg.content or ""))
            elif msg.role == "system":
                lc_messages.append(SystemMessage(content=msg.content or ""))
            elif msg.role == "tool":
                lc_messages.append(ToolMessage(
                    content=msg.content or "",
                    tool_call_id=msg.tool_call_id or "",
                    name=msg.name or ""
                ))
        return lc_messages

    async def run_chat(self, request: ChatCompletionRequest) -> AsyncGenerator[ChatCompletionChunk, None]:
        """Runs the agent and yields OpenAI-compatible chunks."""
        self._ensure_initialized()
        
        # 1. Convert Inputs
        input_messages = self._convert_messages(request.messages)
        
        # 2. Convert external tools from request
        external_tools = []
        if request.tools:
            for tool in request.tools:
                external_tools.append(tool.model_dump())
        
        try:
            graph_input = {
                "messages": input_messages,
                "external_tools": external_tools if external_tools else None
            }

            for event in self.runner.run(graph_input):
                logger.info(f"Graph event received details: {event}")
                for node, details in event.items():
                    # Check for pending tool calls (from ExternalToolExecutor)
                    pending_calls = details.get("pending_tool_calls", [])
                    if pending_calls:
                        # Yield tool calls in OpenAI format
                        from ..schemas.chat import ToolCall, FunctionCall
                        tool_call_objs = []
                        for pc in pending_calls:
                            tool_call_objs.append(ToolCall(
                                id=pc.get("id", f"call_{hash(pc.get('function', {}).get('name', ''))}"),
                                type="function",
                                function=FunctionCall(
                                    name=pc.get("function", {}).get("name", ""),
                                    arguments=pc.get("function", {}).get("arguments", "{}")
                                )
                            ))
                        
                        yield ChatCompletionChunk(
                            model=request.model,
                            choices=[
                                ChoiceDelta(
                                    index=0,
                                    delta=DeltaMessage(tool_calls=tool_call_objs),
                                    finish_reason="tool_calls"
                                )
                            ]
                        )
                        return  # Early return as we need client to execute tools
                    
                    # Handle message outputs from ANY node
                    messages = details.get("messages", [])
                    if not isinstance(messages, list):
                        messages = [messages]

                    for msg in messages:
                        content = ""
                        if hasattr(msg, "content"):
                            content = msg.content
                        elif isinstance(msg, str):
                            content = msg
                        
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
            logger.error(f"Error in adapter run: {e}", exc_info=True)
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
        self._ensure_initialized()
        
        input_messages = self._convert_messages(request.messages)
        full_content = []
        
        try:
            graph_input = {"messages": input_messages}
            
            for event in self.runner.run(graph_input):
                 for node, details in event.items():
                    messages = details.get("messages", [])
                    if not isinstance(messages, list):
                        messages = [messages]
                        
                    for msg in messages:
                        content = ""
                        if hasattr(msg, "content"):
                            content = msg.content
                        elif isinstance(msg, str):
                            content = msg
                            
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
                    prompt_tokens=0, 
                    completion_tokens=0,
                    total_tokens=0
                )
            )

        except Exception as e:
            logger.error(f"Error in adapter run sync: {e}", exc_info=True)
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
