"""
Tests for OpenAI API Plugin Pydantic Schemas.
"""

from kor_plugin_openai_api.schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    Message
)

def test_chat_completion_request_serialization():
    """Test that a request serialization works."""
    req = ChatCompletionRequest(
        model="kor-agent-v1",
        messages=[
            Message(role="user", content="Hello")
        ]
    )
    data = req.model_dump()
    assert data["model"] == "kor-agent-v1"
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][0]["content"] == "Hello"

def test_chat_completion_response_serialization():
    """Test that a response serialization works."""
    # We construct a partial object since many fields have defaults
    # But for a real response, we usually fill choices
    from kor_plugin_openai_api.schemas.chat import Choice, Message
    
    res = ChatCompletionResponse(
        model="kor-agent-v1",
        choices=[
            Choice(
                index=0,
                message=Message(role="assistant", content="Hi there"),
                finish_reason="stop"
            )
        ]
    )
    
    data = res.model_dump()
    assert data["object"] == "chat.completion"
    assert len(data["choices"]) == 1
    assert data["choices"][0]["message"]["content"] == "Hi there"
