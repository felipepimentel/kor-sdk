"""
Comprehensive verification of Persistence, Search, and Telemetry.
"""
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from kor_core.agent.persistence import get_sqlite_checkpointer
from kor_core.agent.graph import create_graph
from kor_core import GraphRunner
from kor_core.kernel import Kernel

def verify_all():
    print("=== Professional Infrastructure Verification ===")
    
    # 1. Setup Environment
    thread_id = "prof-test-999"
    trace_file = Path.home() / ".kor" / "telemetry" / "trace.jsonl"
    if trace_file.exists():
        trace_file.unlink() # Start fresh
        
    print(f"Telemetry file: {trace_file}")
    
    # 2. Boot Kernel (This triggers telemetry setup)
    print("Booting Kernel...")
    kernel = Kernel()
    kernel.boot()
    
    # 3. Test Cycle with Mocks
    # We patch supervisor_node to test transitions
    with patch("kor_core.agent.graph.supervisor_node") as mock_sup:
        checkpointer = get_sqlite_checkpointer()
        graph = create_graph(checkpointer=checkpointer)
        runner = GraphRunner(graph=graph)
        
        # Turn 1: Route to Explorer (Discovery Test)
        mock_sup.side_effect = [{"next_step": "Explorer"}, {"next_step": "FINISH"}]
        
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

if __name__ == "__main__":
    verify_all()
