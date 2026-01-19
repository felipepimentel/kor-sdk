import sys
import asyncio
from pathlib import Path
import os

# Ensure we can import kor_core
sdk_root = Path("/home/pimentel/Workspace/kor-sdk")
sys.path.append(str(sdk_root / "packages/kor-core/src"))
sys.path.append(str(sdk_root / "plugins/kor-plugin-code-graph/src")) # For the tool

from langchain_core.messages import HumanMessage
from kor_core.kernel import get_kernel
from kor_core.agent.graph import create_graph
from langgraph.checkpoint.memory import MemorySaver

async def run_verification():
    print("Booting Kernel...")
    kernel = get_kernel()
    kernel.boot()
    
    # Force override config to ensure our new agents are active
    kernel.config.agent.supervisor_members = ["Architect", "Coder", "Reviewer", "Researcher", "Explorer"]
    
    print("Creating Graph...")
    graph = create_graph(checkpointer=MemorySaver())
    
    print("\n--- Starting Verification Interaction ---\n")
    inputs = {
        "messages": [HumanMessage(content="Create a new Button component following the design system.", name="User")]
    }
    
    # We will try to run the graph. 
    # Expectation: 
    # 1. Supervisor routes to Architect (or Architect is picked if defined? Current Supervisor routes to FINISH or configured members)
    # Wait, existing Supervisor mock logic routes to "Coder" if "code" is in message.
    # It routes to "FINISH" if not.
    # Supervisor PROMPT needs to know about Architect.
    # The default supervisor prompt (if LLM is missing) uses simple heuristics.
    # I should patch the heuristic in nodes.py if I want the mock to work for "Architect".
    # Or I should force the entry point to Architect for this test?
    
    # Let's see what happens.
    
    step_count = 0
    config = {"configurable": {"thread_id": "test-thread"}}
    async for output in graph.astream(inputs, config=config):
        step_count += 1
        for node_name, state_update in output.items():
            print(f"[{step_count}] Node '{node_name}' executed.")
            if "spec" in state_update:
                print(f"   > Spec Updated: {state_update['spec'][:50]}...")
            if "errors" in state_update:
                print(f"   > Errors Reported: {state_update['errors']}")
            if "files_changed" in state_update:
                print(f"   > Files Changed: {state_update['files_changed']}")
            if "next_step" in state_update:
                print(f"   > Next Step: {state_update['next_step']}")
        
        if step_count >= 5:
            print("Stopping after 5 steps.")
            break

if __name__ == "__main__":
    asyncio.run(run_verification())
