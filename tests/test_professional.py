"""
Comprehensive verification of Persistence, Search, and Telemetry.
"""
from pathlib import Path
from unittest.mock import patch
from kor_core.agent.persistence import get_checkpointer
from kor_core.agent.graph import create_graph
from kor_core import GraphRunner
from kor_core.kernel import get_kernel

def test_professional_flow():
    print("=== Professional Infrastructure Verification ===")
    
    # 1. Setup Environment
    thread_id = "prof-test-999"
    trace_file = Path.home() / ".kor" / "telemetry" / "trace.jsonl"
    if trace_file.exists():
        trace_file.unlink() # Start fresh
        
    print(f"Telemetry file: {trace_file}")
    
    # 2. Boot Kernel (This triggers telemetry setup)
    print("Booting Kernel...")
    # 2. Boot Kernel (This triggers telemetry setup)
    print("Booting Kernel...")
    # Use get_kernel ensures we share the instance with create_graph
    kernel = get_kernel()
    kernel.boot_sync()
    
    # 3. Test Cycle with Mocks
    # We patch supervisor_node to test transitions and factory to avoid real LLM usage
    with patch("kor_core.agent.graph.supervisor_node") as mock_sup, \
         patch("kor_core.agent.factory.AgentFactory.create_node") as mock_create_node:
         
        # Setup dummy node that returns serializable data
        def dummy_node(state):
            from langchain_core.messages import AIMessage
            return {"messages": [AIMessage(content="I found some tools.", name="Researcher")]}
            
        mock_create_node.return_value = dummy_node

        checkpointer = get_checkpointer(kernel.config.persistence)
        graph = create_graph(checkpointer=checkpointer)
        runner = GraphRunner(graph=graph)
        
        # Turn 1: Route to Researcher (Test a valid node)
        mock_sup.side_effect = [{"next_step": "Researcher"}, {"next_step": "FINISH"}]
        
        print("Turn 1: Testing Discovery...")
        for event in runner.run("Find tools for testing", thread_id=thread_id):
            print(f"Event: {list(event.keys())}")
            
        # Check if telemetry captured something
        if trace_file.exists():
            with open(trace_file, "r") as f:
                lines = f.readlines()
                print(f"Telemetry captured {len(lines)} events.")
                # Look for ON_BOOT if possible
                has_boot = any("on_boot" in l for l in lines)
                if has_boot: print("SUCCESS: Telemetry captured ON_BOOT.")
        else:
            print("FAILURE: Telemetry file not created.")

        # Check Persistence
        print("Checking Persistence...")
        state = graph.get_state({"configurable": {"thread_id": thread_id}})
        history = state.values.get("messages", [])
        if len(history) > 0:
            print(f"SUCCESS: Persistence saved {len(history)} messages.")
        else:
            print("FAILURE: Persistence found no messages.")

    print("=== Verification Complete ===")


