"""
Pydantic schemas for OpenAI Chat Completions API.

These models match the official OpenAI API specification for compatibility
with OpenAI SDKs and tools.
"""

from typing import List, Optional, Literal, Union, Any
from pydantic import BaseModel, Field
import time
import uuid


class FunctionCall(BaseModel):
    """Function call in a message."""
    name: str
    arguments: str  # JSON string


class ToolCall(BaseModel):
    """Tool call in a message."""
    id: str = Field(default_factory=lambda: f"call_{uuid.uuid4().hex[:24]}")
    type: Literal["function"] = "function"
    function: FunctionCall


class Message(BaseModel):
    """A message in the conversation."""
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[str] = None
    name: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None  # For tool role messages


class Tool(BaseModel):
    """Tool definition for function calling."""
    type: Literal["function"] = "function"
    function: dict  # name, description, parameters


class ChatCompletionRequest(BaseModel):
    """Request body for /v1/chat/completions endpoint."""
    model: str
    messages: List[Message]
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2)
    top_p: Optional[float] = Field(default=1.0, ge=0, le=1)
    n: Optional[int] = Field(default=1, ge=1)
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = Field(default=0, ge=-2, le=2)
    frequency_penalty: Optional[float] = Field(default=0, ge=-2, le=2)
    user: Optional[str] = None
    tools: Optional[List[Tool]] = None
    tool_choice: Optional[Union[str, dict]] = None


class Usage(BaseModel):
    """Token usage statistics."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class Choice(BaseModel):
    """A completion choice in the response."""
    index: int
    message: Message
    finish_reason: Optional[Literal["stop", "length", "tool_calls", "content_filter"]] = None
    logprobs: Optional[Any] = None


class ChatCompletionResponse(BaseModel):
    """Response body for /v1/chat/completions (non-streaming)."""
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:29]}")
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[Choice]
    usage: Optional[Usage] = None
    system_fingerprint: Optional[str] = None


# --- Streaming Models ---

class DeltaMessage(BaseModel):
    """Delta content in a streaming chunk."""
    role: Optional[Literal["assistant"]] = None
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None


class ChoiceDelta(BaseModel):
    """A streaming choice delta."""
    index: int
    delta: DeltaMessage
    finish_reason: Optional[Literal["stop", "length", "tool_calls", "content_filter"]] = None
    logprobs: Optional[Any] = None


class ChatCompletionChunk(BaseModel):
    """Streaming chunk for Server-Sent Events."""
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:29]}")
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChoiceDelta]
    system_fingerprint: Optional[str] = None
