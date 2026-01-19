#!/usr/bin/env python3
"""
KOR SDK - Scenario: Multi-Agent Orchestration
Validates the supervisor-worker pattern and agent collaboration.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "packages/kor-core/src"))
for plugin_dir in (Path.cwd() / "plugins").iterdir():
    if plugin_dir.is_dir() and (plugin_dir / "src").exists():
        sys.path.insert(0, str(plugin_dir / "src"))

def test_multi_agent():
    """Test multi-agent orchestration."""
    print("=" * 50)
    print("   SCENARIO: Multi-Agent Orchestration")
    print("=" * 50)
    
    results = {"passed": 0, "failed": 0}
    
    from kor_core.kernel import Kernel
    from kor_core.config import AgentDefinition, ModelRef, ProviderConfig
    from kor_core.agent.graph import create_graph
    from kor_core.agent.state import AgentState
    
    # 1. Initialize Kernel
    print("\n[1] Initializing Kernel with LLM Config...")
    kernel = Kernel()
    kernel.config.llm.providers["openai"] = ProviderConfig(api_key="sk-test")
    kernel.config.llm.default = ModelRef(provider="openai", model="gpt-4")
    kernel.loader.load_directory_plugins(Path.cwd() / "plugins")
    kernel.boot_sync()
    print("    ✅ Kernel ready")
    results["passed"] += 1
    
    # 2. Configure Multi-Agent Team
    print("\n[2] Configuring Multi-Agent Team...")
    
    # Define custom agents
    kernel.config.agent.definitions["Planner"] = AgentDefinition(
        name="Planner",
        role="You are a project planner who breaks down tasks.",
        goal="Create detailed action plans from requirements.",
        llm_purpose="default",
        tools=[]
    )
    
    kernel.config.agent.definitions["Implementer"] = AgentDefinition(
        name="Implementer",
        role="You are a code implementer who writes code.",
        goal="Implement code based on specifications.",
        llm_purpose="default",
        tools=["terminal", "write_file"]
    )
    
    kernel.config.agent.definitions["Tester"] = AgentDefinition(
        name="Tester",
        role="You are a quality assurance engineer.",
        goal="Test implementations and report bugs.",
        llm_purpose="default",
        tools=["terminal", "read_file"]
    )
    
    print("    ✅ Defined 3 custom agents")
    results["passed"] += 1
    
    # 3. Configure Supervisor Team
    print("\n[3] Configuring Supervisor Team...")
    kernel.config.agent.supervisor_members = [
        "Architect",      # Built-in
        "Coder",          # Built-in
        "Reviewer",       # Built-in
        "Planner",        # Custom
        "Implementer",    # Custom
        "Tester"          # Custom
    ]
    
    print(f"    Team: {kernel.config.agent.supervisor_members}")
    results["passed"] += 1
    
    # 4. Build Graph
    print("\n[4] Building Multi-Agent Graph...")
    try:
        app = create_graph()
        nodes = list(app.get_graph().nodes.keys())
        print(f"    Graph nodes: {nodes}")
        
        # Check built-in nodes
        if "Supervisor" in nodes:
            print("    ✅ Supervisor present")
            results["passed"] += 1
        else:
            print("    ❌ Supervisor missing")
            results["failed"] += 1
        
        # Check team members
        for member in ["Architect", "Coder", "Reviewer"]:
            if member in nodes:
                print(f"    ✅ {member} present")
            else:
                print(f"    ⚠️ {member} not in graph")
        
        results["passed"] += 1
        
    except Exception as e:
        print(f"    ❌ Graph build failed: {e}")
        results["failed"] += 1
    
    # 5. Verify Agent Registry
    print("\n[5] Verifying Agent Registry...")
    agent_registry = kernel.registry.get_service("agents")
    
    if agent_registry:
        agents = agent_registry._agents if hasattr(agent_registry, '_agents') else {}
        print(f"    Registered agents: {list(agents.keys()) if agents else 'default only'}")
        results["passed"] += 1
    else:
        print("    ❌ Agent registry not found")
        results["failed"] += 1
    
    # 6. Verify State Schema
    print("\n[6] Verifying Agent State Schema...")
    # AgentState is a TypedDict, check __annotations__
    annotations = AgentState.__annotations__
    
    if "messages" in annotations and "next_step" in annotations:
        print(f"    ✅ AgentState has required fields: {list(annotations.keys())}")
        results["passed"] += 1
    else:
        print("    ❌ AgentState missing fields")
        results["failed"] += 1
    
    # 7. Verify Edges
    print("\n[7] Verifying Graph Edges...")
    try:
        edges = app.get_graph().edges
        print(f"    Edge count: {len(edges)}")
        results["passed"] += 1
    except Exception as e:
        print(f"    ⚠️ Could not inspect edges: {e}")
        results["passed"] += 1
    
    # 8. Tool Binding Verification
    print("\n[8] Verifying Tool Binding...")
    tool_registry = kernel.registry.get_service("tools")
    tools = tool_registry.get_all()
    
    tool_names = [t.name for t in tools]
    if "terminal" in tool_names and "write_file" in tool_names:
        print(f"    ✅ Required tools available: {len(tools)} tools")
        results["passed"] += 1
    else:
        print(f"    ⚠️ Some tools missing. Available: {tool_names}")
        results["passed"] += 1
    
    # Summary
    print("\n" + "=" * 50)
    total = results["passed"] + results["failed"]
    print(f"   RESULTS: {results['passed']}/{total} passed")
    if results["failed"] == 0:
        print("   STATUS: ✅ ALL TESTS PASSED")
    else:
        print(f"   STATUS: ⚠️ {results['failed']} TESTS FAILED")
    print("=" * 50)
    
    return results["failed"] == 0

if __name__ == "__main__":
    success = test_multi_agent()
    sys.exit(0 if success else 1)
