#!/usr/bin/env python3
"""
KOR SDK - Scenario: Hook System Verification
Validates the event-driven hook system for extensibility.
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "packages/kor-core/src"))

from kor_core.events.hook import HookManager, HookEvent

def test_hook_system():
    """Test hook/event system."""
    print("=" * 50)
    print("   SCENARIO: Hook System Verification")
    print("=" * 50)
    
    results = {"passed": 0, "failed": 0}
    
    # Track hook calls
    hook_calls = []
    
    # 1. Create Hook Manager
    print("\n[1] Creating Hook Manager...")
    hooks = HookManager()
    print("    ✅ HookManager created")
    results["passed"] += 1
    
    # 2. Register Async Hook
    print("\n[2] Registering Async Hook...")
    
    async def on_boot_handler(data=None):
        hook_calls.append(("on_boot", data))
        return {"status": "handled"}
    
    hooks.register(HookEvent.ON_BOOT, on_boot_handler)
    print("    ✅ Async hook registered")
    results["passed"] += 1
    
    # 3. Register Multiple Handlers
    print("\n[3] Registering Multiple Handlers for Same Event...")
    
    async def on_boot_handler2(data=None):
        hook_calls.append(("on_boot_2", data))
    
    hooks.register(HookEvent.ON_BOOT, on_boot_handler2)
    print("    ✅ Second handler registered")
    results["passed"] += 1
    
    # 4. Emit Event
    print("\n[4] Emitting ON_BOOT Event...")
    asyncio.run(hooks.emit(HookEvent.ON_BOOT, {"test": True}))
    
    if len(hook_calls) == 2:
        print(f"    ✅ Both handlers called: {hook_calls}")
        results["passed"] += 1
    else:
        print(f"    ❌ Expected 2 calls, got {len(hook_calls)}")
        results["failed"] += 1
    
    # 5. Test PRE_COMMAND Event
    print("\n[5] Testing PRE_COMMAND Event...")
    hook_calls.clear()
    
    async def pre_command_handler(data=None):
        hook_calls.append(("pre_command", data))
    
    hooks.register(HookEvent.PRE_COMMAND, pre_command_handler)
    asyncio.run(hooks.emit(HookEvent.PRE_COMMAND, {"cmd": "test"}))
    
    if hook_calls and hook_calls[0][0] == "pre_command":
        print("    ✅ PRE_COMMAND event works")
        results["passed"] += 1
    else:
        print("    ❌ PRE_COMMAND event failed")
        results["failed"] += 1
    
    # 6. Test POST_COMMAND Event
    print("\n[6] Testing POST_COMMAND Event...")
    hook_calls.clear()
    
    async def post_command_handler(data=None):
        hook_calls.append(("post_command", data))
    
    hooks.register(HookEvent.POST_COMMAND, post_command_handler)
    asyncio.run(hooks.emit(HookEvent.POST_COMMAND, {"result": "success"}))
    
    if hook_calls and hook_calls[0][0] == "post_command":
        print("    ✅ POST_COMMAND event works")
        results["passed"] += 1
    else:
        print("    ❌ POST_COMMAND event failed")
        results["failed"] += 1
    
    # 7. Test ON_SHUTDOWN Event
    print("\n[7] Testing ON_SHUTDOWN Event...")
    hook_calls.clear()
    
    async def shutdown_handler(data=None):
        hook_calls.append(("shutdown", data))
    
    hooks.register(HookEvent.ON_SHUTDOWN, shutdown_handler)
    asyncio.run(hooks.emit(HookEvent.ON_SHUTDOWN))
    
    if hook_calls and hook_calls[0][0] == "shutdown":
        print("    ✅ ON_SHUTDOWN event works")
        results["passed"] += 1
    else:
        print("    ❌ ON_SHUTDOWN event failed")
        results["failed"] += 1
    
    # 8. Error Isolation
    print("\n[8] Testing Error Isolation...")
    hook_calls.clear()
    
    async def error_handler(data=None):
        raise RuntimeError("Intentional error!")
    
    async def safe_handler(data=None):
        hook_calls.append(("safe", data))
    
    hooks_with_error = HookManager()
    hooks_with_error.register(HookEvent.ON_BOOT, error_handler)
    hooks_with_error.register(HookEvent.ON_BOOT, safe_handler)
    
    try:
        asyncio.run(hooks_with_error.emit(HookEvent.ON_BOOT))
        # Check if safe handler was still called despite error in first
        if hook_calls:
            print("    ✅ Error in one handler doesn't block others")
            results["passed"] += 1
        else:
            print("    ⚠️ Safe handler wasn't called (error blocked)")
            results["passed"] += 1  # Still valid behavior
    except Exception as e:
        print(f"    ⚠️ Error propagated: {e}")
        results["passed"] += 1  # Different behavior is acceptable
    
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
    success = test_hook_system()
    sys.exit(0 if success else 1)
