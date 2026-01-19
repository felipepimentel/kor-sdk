import sys
import asyncio
from pathlib import Path
import shutil

# Ensure we can import kor_core
sdk_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(sdk_root / "packages/kor-core/src"))
sys.path.insert(0, str(sdk_root / "plugins/kor-plugin-code-graph/src")) 

from langchain_core.messages import HumanMessage
from kor_core.kernel import get_kernel
from kor_core.agent.graph import create_graph
from langgraph.checkpoint.memory import MemorySaver

async def run_scenario():
    print("--- SCENARIO: Create Python Project (gpt-4o-mini) ---")
    
    # 1. Boot Kernel
    import kor_core
    import kor_core.agent.nodes
    print(f"DEBUG: kor_core path: {kor_core.__file__}")
    print(f"DEBUG: kor_core.agent.nodes path: {kor_core.agent.nodes.__file__}")
    
    # 2. Add OpenAI Plugin Path & Register Provider
    sys.path.insert(0, str(sdk_root / "plugins/kor-plugin-llm-openai/src"))
    from kor_plugin_llm_openai.provider import OpenAIProvider
    
    kernel = get_kernel()
    await kernel.boot()
    
    # Manual Registration since we missed plugin loading
    kernel.llm_registry.register(OpenAIProvider())
    
    # 2. Configure for Hub & Spoke
    kernel.config.agent.supervisor_members = ["Architect", "Coder", "Reviewer"]
    
    # 3. Configure Mock Model for Deterministic Validation (and cost saving)
    from typing import Any, List, Optional
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.messages import AIMessage, BaseMessage
    from langchain_core.outputs import ChatResult, ChatGeneration
    from kor_core.config import ModelRef
    
    class MockScenarioLLM(BaseChatModel):
        def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, run_manager=None, **kwargs: Any) -> ChatResult:
            last_msg = messages[-1].content
            
            # 1. Architect Response
            if "You are the **Architect**" in str(messages[0].content) or "Architect" in last_msg:
                content = (
                    "SPECIFICATION for neural-data-processor:\n"
                    "1. src/neural_data_processor/__init__.py\n"
                    "2. src/neural_data_processor/main.py\n"
                    "3. README.md"
                )
                return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])

            # 2. Coder Response
            if "You are a Coder" in str(messages[0].content):
                # We need to return TOOL CALLS for WriteFile
                tool_calls = [
                    {
                        "name": "write_file",
                        "args": {"path": str(output_dir / "README.md"), "content": "# Neural Data Processor\n"},
                        "id": "call_1"
                    },
                    {
                        "name": "write_file",
                        "args": {"path": str(output_dir / "src/neural_data_processor/__init__.py"), "content": ""},
                        "id": "call_2"
                    },
                    {
                        "name": "write_file",
                        "args": {"path": str(output_dir / "src/neural_data_processor/main.py"), "content": "print('Hello Neural World')"},
                        "id": "call_3"
                    }
                ]
                msg = AIMessage(content="Creating files...", tool_calls=tool_calls)
                return ChatResult(generations=[ChatGeneration(message=msg)])

            # 3. Reviewer Response
            if "You are the **Reviewer**" in str(messages[0].content):
                return ChatResult(generations=[ChatGeneration(message=AIMessage(content="PASS"))])
                
            # Default
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content="I am a mock agent."))])

        @property
        def _llm_type(self) -> str:
            return "mock-scenario"

        def bind_tools(self, tools: list, **kwargs):
            return self

        def with_structured_output(self, schema, **kwargs):
            # Return a runnable that mimics the Supervisor routing logic
            from langchain_core.runnables import RunnableLambda
            
            def routing_logic(input_val):
                # input_val is usually a prompt value or list of messages
                # We extract the last message content
                msgs = []
                last_significant_msg = ""
                
                if hasattr(input_val, "to_messages"):
                    msgs = input_val.to_messages()
                elif isinstance(input_val, list):
                    msgs = input_val
                else:
                    last_significant_msg = str(input_val)

                # Convert all previous content to a big string for search context
                full_history = "\n".join([m.content for m in msgs]) if msgs else last_significant_msg
                
                print(f"[DEBUG Router] History Len: {len(full_history)}")

                # Heuristic Routing for Scenario
                # 1. New Request -> Architect
                if "Create a new Python project" in full_history and "SPECIFICATION" not in full_history:
                    return {"next_step": "Architect"}
                    
                # 2. Spec Exists -> Coder (only if Coder hasn't acted yet)
                if "SPECIFICATION" in full_history:
                    # Check if Coder has already acted (look for tool output or Coder message)
                    if "Creating files..." in full_history:
                        # If Coder finished, go to Reviewer
                        if "PASS" not in full_history:
                             return {"next_step": "Reviewer"}
                        else:
                             return {"next_step": "FINISH"}
                    
                    return {"next_step": "Coder"}

                if "PASS" in full_history:
                    return {"next_step": "FINISH"}
                
                # Fallback
                return {"next_step": "FINISH"}

            return RunnableLambda(routing_logic)

    # Register Mock Provider dynamically
    from kor_core.llm.provider import BaseLLMProvider
    
    class MockProvider(BaseLLMProvider):
         @property
         def name(self) -> str:
             return "mock"
             
         def get_chat_model(self, model_name: str, config: dict) -> BaseChatModel:
             return MockScenarioLLM()

    # Create instance and register
    kernel.llm_registry.register(MockProvider())
    
    # Ensure provider has a config entry (even if empty)
    from kor_core.config import ProviderConfig
    kernel.config.llm.providers["mock"] = ProviderConfig()
    
    kernel.config.llm.default = ModelRef(
        provider="mock",
        model="scenario-1",
        temperature=0.0
    )
    
    print("Model Configured: Mock Scenario (Cost Effective)")
    
    # 4. Define Output Path
    output_dir = sdk_root / "examples/out/neural-data-processor"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    print(f"Target Directory: {output_dir}")
    
    # 5. Create Graph
    graph = create_graph(checkpointer=MemorySaver())
    
    # 6. Run Interaction
    prompt = (
        f"Create a new Python project named 'neural-data-processor'. "
        f"Root path: {output_dir}. "
        "It MUST have: "
        "- src/neural_data_processor/__init__.py "
        "- src/neural_data_processor/main.py (prints 'Hello Neural World') "
        "- README.md (Title: Neural Data Processor). "
        "Follow best practices."
    )
    
    inputs = {
        "messages": [HumanMessage(content=prompt, name="User")]
    }
    
    config = {"configurable": {"thread_id": "scenario-project-1"}}
    
    step_count = 0
    print("\n--- Agent Execution Start ---\n")
    async for output in graph.astream(inputs, config=config):
        step_count += 1
        for node_name, state_update in output.items():
            print(f"[{step_count}] Node '{node_name}'")
            if "spec" in state_update:
                print(f"   > Spec Generated (Len: {len(state_update['spec'])})")
            if "files_changed" in state_update and state_update['files_changed']:
                print(f"   > Files Created: {state_update['files_changed']}")
            if "errors" in state_update:
                print(f"   > Reviewer Feedback: {state_update['errors']}")
            if "messages" in state_update:
                msgs = state_update['messages']
                for m in msgs:
                    print(f"   > Msg [{m.name}]: {m.content[:200]}...")
                
        if step_count > 20: # Safety break
            print("Stopping after 20 steps (Safety limit).")
            break
            
    # 7. Validation
    print("\n--- Validation ---")
    expected_files = [
        output_dir / "README.md",
        output_dir / "src/neural_data_processor/main.py",
        output_dir / "src/neural_data_processor/__init__.py"
    ]
    
    all_passed = True
    for f in expected_files:
        if f.exists():
            print(f"[PASS] {f.name} exists.")
            if f.name == "main.py":
                content = f.read_text()
                if "Hello Neural World" in content:
                    print("   > Content verification passed.")
                else:
                    print("   > Content verification FAILED.")
                    all_passed = False
        else:
            print(f"[FAIL] {f.name} missing.")
            all_passed = False
            
    if all_passed:
        print("\nSUCCESS: Project created successfully with architecture flow.")
    else:
        print("\nFAILURE: Project creation incomplete.")

if __name__ == "__main__":
    asyncio.run(run_scenario())
