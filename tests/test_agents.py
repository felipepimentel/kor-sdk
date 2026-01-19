"""
Verify Agent Registry and Dynamic Loading.
"""
from kor_core import Kernel

import pytest

@pytest.mark.asyncio
async def test_agents():
    print("Booting Kernel...")
    k = Kernel()
    await k.boot()
    
    registry = k.registry.get_service("agents")
    agents = registry.list_agents()
    print(f"Registered Agents: {list(agents.keys())}")
    
    # Verify default agent
    if "default-supervisor" not in agents:
        print("FAILURE: default-supervisor not found.")
        return
        
    print("SUCCESS: default-supervisor found.")
    
    # Verify loading graph
    try:
        graph = registry.load_graph("default-supervisor")
        print(f"SUCCESS: Loaded graph object: {type(graph)}")
    except Exception as e:
        print(f"FAILURE: Could not load graph: {e}")

if __name__ == "__main__":
    test_agents()
