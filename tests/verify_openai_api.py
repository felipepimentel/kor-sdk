"""
Integration Check for OpenAI API Plugin.

This script acts as a manual client using the official OpenAI SDK
to verify that our server is working correctly.
"""

import os
import sys
import openai
from kor_plugin_openai_api.schemas.chat import ChatCompletionChunk

def test_integration():
    """Run a simple chat completion against the local server."""
    
    # Configure client to point to local KOR
    client = openai.OpenAI(
        base_url="http://localhost:8001/v1",
        api_key="sk-test-key-not-checked-yet"
    )
    
    print("--- Testing /v1/models ---")
    try:
        models = client.models.list()
        print(f"Models: {[m.id for m in models]}")
        assert "kor-agent-v1" in [m.id for m in models]
    except Exception as e:
        print(f"FAILED to list models: {e}")
        return

    print("\n--- Testing /v1/chat/completions (Non-Streaming) ---")
    try:
        response = client.chat.completions.create(
            model="kor-agent-v1",
            messages=[{"role": "user", "content": "List files in the current dir"}]
        )
        print(f"Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"FAILED Non-Streaming Chat: {e}")

    print("\n--- Testing /v1/chat/completions (Streaming) ---")
    try:
        stream = client.chat.completions.create(
            model="kor-agent-v1",
            messages=[{"role": "user", "content": "List files please"}],
            stream=True
        )
        print("Stream: ", end="")
        for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            print(content, end="", flush=True)
        print("\n(Stream Done)")
    except Exception as e:
        print(f"FAILED Streaming Chat: {e}")

if __name__ == "__main__":
    # Ensure server is running before executing this
    try:
        test_integration()
    except Exception as e:
        print(f"Integration Check Failed: {e}")
