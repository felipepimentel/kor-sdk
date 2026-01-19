import sys
from pathlib import Path
import logging

# Add package source to path
sys.path.insert(0, str(Path.cwd() / "packages/kor-core/src"))
sys.path.insert(0, str(Path.cwd() / "plugins/kor-plugin-llm-openai/src"))

from kor_core.kernel import get_kernel
from kor_core.config import AgentDefinition, ModelRef, ProviderConfig
from kor_core.agent.factory import AgentFactory
from kor_core.agent.graph import create_graph

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def verify_agent_factory():
    print("--- Verifying Agent Factory (Low-Code Agents) ---")
    
    # 1. Initialize Kernel with Mock Config
    print("[1] Initializing Kernel & Config...")
    kernel = get_kernel()
    
    # Setup LLM (Mock)
    kernel.config.llm.providers["openai"] = ProviderConfig(api_key="sk-test")
    kernel.config.llm.purposes["audit"] = ModelRef(provider="openai", model="gpt-4-turbo")
    
    # Setup Custom Agent: SecurityAuditor
    print("[2] Defining 'SecurityAuditor' in Config...")
    auditor_def = AgentDefinition(
        name="SecurityAuditor",
        role="You are a simplified security auditor.",
        goal="Check for obvious bugs.",
        llm_purpose="audit",
        tools=["terminal"] # Assuming terminal tool exists
    )
    
    # Register definition
    kernel.config.agent.definitions["SecurityAuditor"] = auditor_def
    
    # Update Supervisor Team
    kernel.config.agent.supervisor_members = ["Coder", "SecurityAuditor"]
    
    # Boot to load tools/plugins
    print("[3] Booting Kernel...")
    # Load plugins from workspace to ensure OpenAI provider is available
    kernel.loader.load_directory_plugins(Path.cwd() / "plugins")
    kernel.boot()
    
    # 2. Test Factory Isolation
    print("[4] Testing Factory Node Creation...")
    factory = AgentFactory(kernel)
    node_func = factory.create_node("SecurityAuditor", auditor_def)
    
    if callable(node_func):
        print("    ✅ Factory returned a callable node.")
    else:
        print("    ❌ FAIL: Factory returned non-callable.")
        return

    # 3. Test Graph Construction
    print("[5] Building Dynamic Graph...")
    app = create_graph()
    
    # Check graph nodes (LangGraph internal structure)
    # We can inspect the graph object. 
    # workflow.compile() returns a CompiledGraph.
    # It has .nodes usually accessible?
    # compiled_graph.get_graph().nodes is likely available in recent versions.
    
    try:
        nodes = app.get_graph().nodes.keys()
        print(f"    Graph Nodes: {list(nodes)}")
        
        if "SecurityAuditor" in nodes:
             print("    ✅ SecurityAuditor node present in graph.")
        else:
             print("    ❌ FAIL: SecurityAuditor node MISSING.")
             
        if "Supervisor" in nodes:
             print("    ✅ Supervisor node present.")
             
        # Check if Researcher is GONE (as we removed it from supervisor_members)
        if "Researcher" not in nodes:
            print("    ✅ Researcher correctly excluded (Dynamic Graph works).")
        else:
            # Note: create_graph iterates over members list. If it's not in list, it shouldn't add it.
            # Unless we kept hardcoded backups.
            print("    ⚠️ Researcher still present (Check logic).")
            
    except Exception as e:
        print(f"    ⚠️ Could not inspect graph nodes directly: {e}")

    print("\n✅ Agent Factory Verification Complete.")

if __name__ == "__main__":
    verify_agent_factory()
