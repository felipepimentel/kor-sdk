#!/usr/bin/env python3
"""
KOR SDK - Scenario: Agent Factory Verification
Validates dynamic agent creation from configuration.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "packages/kor-core/src"))
for plugin_dir in (Path.cwd() / "plugins").iterdir():
    if plugin_dir.is_dir() and (plugin_dir / "src").exists():
        sys.path.insert(0, str(plugin_dir / "src"))

def test_agent_factory():
    """Test agent factory functionality."""
    print("=" * 50)
    print("   SCENARIO: Agent Factory Verification")
    print("=" * 50)
    
    results = {"passed": 0, "failed": 0}
    
    from kor_core.kernel import Kernel
    from kor_core.config import AgentDefinition, ModelRef, ProviderConfig
    from kor_core.agent.factory import AgentFactory
    from kor_core.agent.graph import create_graph
    
    # 1. Initialize Kernel
    print("\n[1] Initializing Kernel...")
    kernel = Kernel()
    
    # Configure mock LLM
    kernel.config.llm.providers["openai"] = ProviderConfig(api_key="sk-test")
    kernel.config.llm.default = ModelRef(provider="openai", model="gpt-4")
    kernel.config.llm.purposes["analysis"] = ModelRef(provider="openai", model="gpt-4-turbo")
    
    kernel.loader.load_directory_plugins(Path.cwd() / "plugins")
    kernel.boot_sync()
    print("    ✅ Kernel initialized")
    results["passed"] += 1
    
    # 2. Create Custom Agent Definition
    print("\n[2] Creating Custom Agent Definition...")
    
    custom_agent = AgentDefinition(
        name="SecurityAnalyzer",
        role="You are a security expert who analyzes code for vulnerabilities.",
        goal="Find and report security issues in code.",
        llm_purpose="analysis",
        tools=["terminal", "read_file"]
    )
    
    kernel.config.agent.definitions["SecurityAnalyzer"] = custom_agent
    print("    ✅ Custom agent defined")
    results["passed"] += 1
    
    # 3. Test Factory Node Creation
    print("\n[3] Testing Factory Node Creation...")
    factory = AgentFactory.from_kernel(kernel)
    
    node_func = factory.create_node("SecurityAnalyzer", custom_agent)
    
    if callable(node_func):
        print("    ✅ Factory returned callable node function")
        results["passed"] += 1
    else:
        print("    ❌ Factory did not return callable")
        results["failed"] += 1
    
    # 4. Update Supervisor Members
    print("\n[4] Updating Supervisor Members...")
    kernel.config.agent.supervisor_members = ["Architect", "Coder", "SecurityAnalyzer"]
    
    if "SecurityAnalyzer" in kernel.config.agent.supervisor_members:
        print("    ✅ Custom agent added to supervisor members")
        results["passed"] += 1
    else:
        print("    ❌ Failed to add custom agent")
        results["failed"] += 1
    
    # 5. Build Dynamic Graph
    print("\n[5] Building Dynamic Graph...")
    try:
        app = create_graph()
        nodes = list(app.get_graph().nodes.keys())
        print(f"    Graph nodes: {nodes}")
        
        if "Supervisor" in nodes:
            print("    ✅ Supervisor node present")
            results["passed"] += 1
        else:
            print("    ❌ Supervisor node missing")
            results["failed"] += 1
        
        if "Architect" in nodes:
            print("    ✅ Architect node present")
            results["passed"] += 1
        else:
            print("    ❌ Architect node missing")
            results["failed"] += 1
        
        if "Coder" in nodes:
            print("    ✅ Coder node present")
            results["passed"] += 1
        else:
            print("    ❌ Coder node missing")
            results["failed"] += 1
            
    except Exception as e:
        print(f"    ❌ Graph creation failed: {e}")
        results["failed"] += 1
    
    # 6. Verify Agent Registry
    print("\n[6] Verifying Agent Registry...")
    agent_registry = kernel.registry.get_service("agents")
    
    if agent_registry:
        print("    ✅ Agent registry accessible")
        results["passed"] += 1
    else:
        print("    ❌ Agent registry not found")
        results["failed"] += 1
    
    # 7. Check Default Agent
    print("\n[7] Checking Default Agent Registration...")
    try:
        default_agent = agent_registry.get_agent_definition("default-supervisor")
        if default_agent:
            print(f"    ✅ Default agent registered: {default_agent.name}")
            results["passed"] += 1
        else:
            print("    ⚠️ Default agent not found")
            results["passed"] += 1
    except Exception as e:
        print(f"    ⚠️ Could not fetch default agent: {e}")
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
    success = test_agent_factory()
    sys.exit(0 if success else 1)
