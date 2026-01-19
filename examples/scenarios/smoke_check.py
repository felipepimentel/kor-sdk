"""
Smoke Check Scenario for KOR SDK Refactoring
Verifies that the public API (Kor facade) works as expected after core refactoring.
"""

import sys
import asyncio
from kor_core import Kor
from kor_core.events import HookEvent

async def main():
    print("=== KOR SDK Smoke Check ===")
    
    # 1. Initialize Facade
    print("[1] Initializing Kor Facade...")
    kor = Kor()
    
    # 2. Register a hook (verify events unified)
    print("[2] Registering hooks...")
    hook_called = False
    async def on_boot():
        nonlocal hook_called
        print("    -> Hook ON_BOOT triggered!")
        hook_called = True
        
    kor.hooks.register(HookEvent.ON_BOOT, on_boot)
    
    # 3. Boot
    print("[3] Booting Kernel...")
    await kor.boot_async()
    
    if not hook_called:
        print("ERROR: Hook not triggered!")
        sys.exit(1)
        
    if not kor.is_active:
        print("ERROR: Kernel not reported as active!")
        sys.exit(1)
        
    print("    -> Kernel booted and active.")

    # 4. Verify Components
    print("[4] Verifying Components...")
    
    # LLM (unified)
    try:
        model = kor.llm.get_model("default")
        print(f"    -> LLM Provider operational: {type(model).__name__}")
    except Exception as e:
        print(f"    -> WARNING: LLM check failed (expected if no API key): {e}")

    # Tools
    tools = kor.tools.get_all()
    tool_names = [t.name for t in tools]
    print(f"    -> Tools loaded: {len(tools)} tools available: {tool_names}")
    if "terminal_run" not in tool_names and "terminal" not in tool_names:
        print("ERROR: Core tools (terminal) not found!")
        sys.exit(1)
        
    # Search (unified)
    # We verify we can search tools
    results = kor.tools.search("execute commands")
    print(f"    -> Tool Search 'execute commands': Found {len(results)} results.")
    if not results:
        print("WARNING: Search returned no results.")

    # 5. Verify Agent Registry
    agents = kor.agents.get_all()
    print(f"    -> Agents loaded: {len(agents)}")
    
    print("\n=== SYSTEM HEALTHY (Refactoring Validated) ===")

if __name__ == "__main__":
    asyncio.run(main())
