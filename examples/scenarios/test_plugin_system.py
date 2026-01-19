#!/usr/bin/env python3
"""
KOR SDK - Scenario: Plugin System Verification
Validates that all plugins load correctly and register their services.
"""
import sys
from pathlib import Path

# Add package paths
sys.path.insert(0, str(Path.cwd() / "packages/kor-core/src"))
for plugin_dir in (Path.cwd() / "plugins").iterdir():
    if plugin_dir.is_dir() and (plugin_dir / "src").exists():
        sys.path.insert(0, str(plugin_dir / "src"))

from kor_core.kernel import Kernel  # noqa: E402

def test_plugin_system():
    """Test that all plugins discover and load correctly."""
    print("=" * 50)
    print("   SCENARIO: Plugin System Verification")
    print("=" * 50)
    
    results = {"passed": 0, "failed": 0}
    
    # 1. Kernel Instantiation
    print("\n[1] Creating Kernel...")
    kernel = Kernel()
    print("    ✅ Kernel instantiated")
    results["passed"] += 1
    
    # 2. Plugin Discovery
    print("\n[2] Discovering Plugins from Directory...")
    kernel.loader.load_directory_plugins(Path.cwd() / "plugins")
    discovered = kernel.loader._discovered_classes
    print(f"    Discovered {len(discovered)} plugin classes")
    
    expected_plugins = [
        "kor-plugin-smart-edit",
        "kor-plugin-llm-openai", 
        "kor-plugin-code-graph",
        "kor-plugin-system-info"
    ]
    
    # Optional plugins that may not load if dependencies are missing
    optional_plugins = [
        "kor-plugin-llm-litellm",
        "kor-plugin-tui",
        "kor-plugin-openai-api"
    ]
    
    # 3. Boot Kernel
    print("\n[3] Booting Kernel...")
    kernel.boot_sync()
    print("    ✅ Kernel booted")
    results["passed"] += 1
    
    # 4. Check Loaded Plugins
    print("\n[4] Verifying Loaded Plugins...")
    loaded = list(kernel.loader._plugins.keys())
    print(f"    Loaded plugins: {loaded}")
    
    for plugin_id in expected_plugins:
        if plugin_id in loaded:
            print(f"    ✅ {plugin_id}")
            results["passed"] += 1
        else:
            print(f"    ❌ MISSING: {plugin_id}")
            results["failed"] += 1
            
    for plugin_id in optional_plugins:
        if plugin_id in loaded:
            print(f"    ✅ {plugin_id} (optional)")
            results["passed"] += 1
        else:
            print(f"    ⚠️  {plugin_id} (optional - dependencies might be missing)")
    
    # 5. Verify LLM Providers
    print("\n[5] Verifying LLM Providers...")
    providers = list(kernel.llm_registry._providers.keys())
    print(f"    Registered providers: {providers}")
    
    # OpenAI is expected as primary
    if "openai" in providers:
        print("    ✅ openai")
        results["passed"] += 1
    else:
        print("    ❌ MISSING: openai")
        results["failed"] += 1
        
    # LiteLLM is optional
    if "litellm" in providers:
        print("    ✅ litellm (optional)")
        results["passed"] += 1
    else:
        print("    ⚠️  litellm (optional - not loaded)")
    
    # 6. Verify Tool Registry
    print("\n[6] Verifying Tool Registry...")
    tool_registry = kernel.registry.get_service("tools")
    tools = tool_registry.get_all()
    print(f"    Registered tools: {len(tools)}")
    
    core_tools = ["terminal", "browser", "read_file", "write_file", "list_dir", "search_tools"]
    for tool_name in core_tools:
        found = any(tool_name in t.name.lower() for t in tools)
        if found:
            print(f"    ✅ {tool_name}")
            results["passed"] += 1
        else:
            print(f"    ⚠️ Not found: {tool_name}")
    
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
    success = test_plugin_system()
    sys.exit(0 if success else 1)
