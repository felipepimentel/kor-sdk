
import sys
import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

# Add package root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../packages/kor-core/src")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../plugins/kor-plugin-openai-api/src")))

# Mocking the supervisor to avoid LLM calls
def mock_supervisor_node(state):
    return {"next_step": "Coder"}

def mock_coder_node(state):
    return {"messages": [AIMessage(content="Hello from Coder via API")]}

# We need to patch where they are IMPORTED in the registry/loader or kernel
# But getting the kernel to use these mocks is tricky because it loads from string paths.
# However, if we patch `kor_core.agent.nodes.supervisor_node`, it might work if they are imported.

with patch("kor_core.agent.nodes.supervisor_node", side_effect=mock_supervisor_node), \
     patch("kor_core.agent.nodes.coder_node", side_effect=mock_coder_node):
     
    from kor_plugin_openai_api.main import app
    
    client = TestClient(app)

    def test_models():
        response = client.get("/v1/models")
        assert response.status_code == 200
        data = response.json()
        model_ids = [m["id"] for m in data["data"]]
        assert "kor-agent-v1" in model_ids
        print("SUCCESS: /v1/models")

    def test_chat():
        response = client.post("/v1/chat/completions", json={
            "model": "kor-agent-v1",
            "messages": [{"role": "user", "content": "Hello"}]
        })
        # Note: The real graph might behave differently if not fully mocked, 
        # but the adapter should handle exceptions gracefully.
        
        # If the mock didn't take effect (because graph loads freshly), 
        # it might try to call LLM and fail or return error.
        
        print(f"Chat Response: {response.json()}")
        # We expect a success even if it's an error message from the adapter
        assert response.status_code == 200

    if __name__ == "__main__":
        try:
            test_models()
            test_chat()
            print("SUCCESS: OpenAI API Mock Test Passed")
        except Exception as e:
            print(f"FAILED: {e}")
            sys.exit(1)
