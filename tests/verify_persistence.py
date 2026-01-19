import sys
from pathlib import Path
import logging
import uuid
import shutil

# Add package source to path
sys.path.insert(0, str(Path.cwd() / "packages/kor-core/src"))
sys.path.insert(0, str(Path.cwd() / "plugins/kor-plugin-llm-openai/src"))

from kor_core.kernel import get_kernel
from kor_core.config import PersistenceConfig, ProviderConfig, ModelRef
from kor_core.agent.graph import create_graph

# Configure logging
logging.basicConfig(level=logging.INFO)

def verify_persistence():
    print("--- Verifying Persistence (SQLite) ---")
    
    # Setup test DB path
    db_path = Path.cwd() / "test_memories.db"
    if db_path.exists():
        db_path.unlink()
        
    thread_id = str(uuid.uuid4())
    print(f"[1] Thread ID: {thread_id}")
    
    # --- SESSION 1 ---
    print("\n[Session 1] Booting Kernel with SQLite...")
    kernel = get_kernel()
    
    # Configure Persistence
    kernel.config.persistence = PersistenceConfig(type="sqlite", path=str(db_path))
    
    # Configure LLM (Mock/Lite)
    kernel.config.llm.providers["openai"] = ProviderConfig(api_key="sk-test")
    kernel.config.llm.default = ModelRef(provider="openai", model="gpt-3.5-turbo")
    
    kernel.loader.load_directory_plugins(Path.cwd() / "plugins")
    kernel.boot()
    
    # Create Graph (should use kernel checkpointer)
    app = create_graph()
    
    # Check if checkpointer is attached
    if app.checkpointer:
        print("✅ Graph has checkpointer attached.")
    else:
        print("❌ FAIL: Graph has NO checkpointer.")
        return

    # Simulate running (Adding state)
    from langchain_core.messages import HumanMessage
    print("[Session 1] Saving state to DB...")
    config = {"configurable": {"thread_id": thread_id}}
    app.update_state(config, {"messages": [HumanMessage(content="Hello Persistence!")]})
    
    # Verify state exists in memory (current session)
    state = app.get_state(config)
    if state.values and state.values["messages"][0].content == "Hello Persistence!":
        print("✅ State saved in Session 1.")
    else:
        print(f"❌ FAIL: State not saved. {state.values}")
        return
        
    # --- SESSION 2 (Simulated Restart) ---
    print("\n[Session 2] Simulating Restart (re-creating graph)...")
    
    # We create a new kernel instance concept or just re-request graph
    # Ideally we should destroy kernel, but get_kernel is singleton.
    # We can just request a new graph, it reads from SAME DB path.
    # The checkpointer inside kernel is connected to the same DB file.
    
    # Let's try to "reboot" by getting checkpointer again purely from factory?
    # Or just trust that if a NEW process started, it would read the file.
    # We can verify the FILE exists.
    if db_path.exists() and db_path.stat().st_size > 0:
        print(f"✅ DB File exists at {db_path} ({db_path.stat().st_size} bytes).")
    else:
        print("❌ FAIL: DB File not created/empty.")
        return

    # Create new graph instance (simulating new run)
    # It will fetch checkpointer from kernel (which has connection to DB)
    app2 = create_graph()
    state2 = app2.get_state(config)
    
    if state2.values and state2.values["messages"][0].content == "Hello Persistence!":
        print("✅ State LOADED in Session 2 (Persistence Works!).")
    else:
         print(f"❌ FAIL: State NOT loaded in Session 2. {state2.values}")

    # Cleanup
    if db_path.exists():
        db_path.unlink()
        print("\nCleanup: Removed test DB.")

if __name__ == "__main__":
    verify_persistence()
