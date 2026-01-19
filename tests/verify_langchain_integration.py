
import os
import sys

# Ensure we can import kor_core if needed, though this script acts as a client
# so it mainly depends on langchain-openai
sys.path.append(os.getcwd())

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
except ImportError:
    print("Error: langchain-openai is required for this verification script.")
    print("Run with: uv run --with langchain-openai --with langchain python tests/verify_langchain_integration.py")
    sys.exit(1)

def verify_integration():
    print("🚀 Starting KOR LangChain Integration Verification")
    
    # 1. Setup Client pointing to KOR
    # We assume KOR is running on port 8000 (default for apps/openai-api/main.py usually, 
    # but let's check if we need to start it first. 
    # Actually, for this script to run, the server must be up.
    # We will assume the user or a separate process runs the server.
    
    api_base = os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
    api_key = os.getenv("OPENAI_API_KEY", "kor-dev-key")
    
    print(f"📡 Connecting to KOR at {api_base}...")
    
    llm = ChatOpenAI(
        base_url=api_base,
        api_key=api_key,
        model="kor-model", # Model name gets passed but KOR might ignore or use it
        temperature=0,
        streaming=True # Test streaming as it's the more complex path
    )
    
    # 2. Test 1: Simple Question
    print("\n🧪 Test 1: Simple Greeting")
    try:
        response = llm.invoke("Hello, who are you?")
        print(f"🤖 KOR Answer: {response.content}")
        assert len(response.content) > 0
        print("✅ Test 1 Passed")
    except Exception as e:
        print(f"❌ Test 1 Failed: {e}")
        return

    # 3. Test 2: Multi-turn Conversation (History)
    print("\n🧪 Test 2: Conversation History")
    messages = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content="My name is Felipe."),
        AIMessage(content="Hello Felipe! How can I help you today?"),
        HumanMessage(content="What is my name?")
    ]
    
    try:
        response = llm.invoke(messages)
        print(f"🤖 KOR Answer: {response.content}")
        if "Felipe" in response.content:
            print("✅ Test 2 Passed (History retained)")
        else:
            print("⚠️ Test 2 Warning: KOR might not have used history correctly.")
    except Exception as e:
        print(f"❌ Test 2 Failed: {e}")
        return
        
    print("\n🎉 Verification Complete! (Phase 1)")

    # 4. Test 3: Client-Side Tool Call
    print("\n🧪 Test 3: Client-Side Tools")
    
    # Define a tool schema
    tools = [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get valid weather for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"}
                },
                "required": ["city"]
            }
        }
    }]
    
    llm_with_tools = llm.bind_tools(tools)
    
    try:
        print("   Asking KOR to check the weather in London...")
        response = llm_with_tools.invoke("What is the weather in London?")
        
        # We expect a tool call
        if response.tool_calls:
            print(f"   Received Tool Call: {response.tool_calls}")
            tc = response.tool_calls[0]
            assert tc['name'] == "get_weather"
            assert "London" in tc['args']['city']
            
            # Simulate returning result
            from langchain_core.messages import ToolMessage
            tool_msg = ToolMessage(tool_call_id=tc['id'], content="Sunny, 25C", name="get_weather")
            
            print("   Sending Tool Result back...")
            # Continue conversation
            final_response = llm_with_tools.invoke(messages + [response, tool_msg])
            print(f"🤖 KOR Final Answer: {final_response.content}")
            
            if "25" in final_response.content or "Sunny" in final_response.content:
                print("✅ Test 3 Passed (Client Tool Used)")
            else:
                 print("⚠️ Test 3 Warning: KOR received tool result but didn't mention it.")
        
        else:
             print(f"❌ Test 3 Failed: No tool call returned. Response: {response.content}")

    except Exception as e:
        print(f"❌ Test 3 Failed with Error: {e}")

    print("\n🎉 Verification Complete (All Phases)!")

if __name__ == "__main__":
    verify_integration()
