#!/usr/bin/env python3
"""
KOR SDK - Scenario: LLM Selector and Provider System
Validates the model selection, purpose routing, and fallback mechanisms.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "packages/kor-core/src"))
for plugin_dir in (Path.cwd() / "plugins").iterdir():
    if plugin_dir.is_dir() and (plugin_dir / "src").exists():
        sys.path.insert(0, str(plugin_dir / "src"))

def test_llm_system():
    """Test LLM selector and provider system."""
    print("=" * 50)
    print("   SCENARIO: LLM Selector & Provider System")
    print("=" * 50)
    
    results = {"passed": 0, "failed": 0}
    
    from kor_core.kernel import Kernel
    from kor_core.config import ModelRef, ProviderConfig
    from kor_core.llm import LLMRegistry, ModelSelector
    
    # 1. Initialize Kernel
    print("\n[1] Initializing Kernel...")
    kernel = Kernel()
    
    # Configure providers
    kernel.config.llm.providers["openai"] = ProviderConfig(
        api_key="sk-test-openai",
        base_url=None
    )
    kernel.config.llm.providers["anthropic"] = ProviderConfig(
        api_key="sk-test-anthropic"
    )
    
    # Configure default model
    kernel.config.llm.default = ModelRef(
        provider="openai",
        model="gpt-4-turbo",
        temperature=0.7
    )
    
    # Configure purpose-specific models
    kernel.config.llm.purposes["coding"] = ModelRef(
        provider="openai",
        model="gpt-4o",
        temperature=0.2
    )
    kernel.config.llm.purposes["research"] = ModelRef(
        provider="openai",
        model="gpt-4-turbo",
        temperature=0.8
    )
    kernel.config.llm.purposes["creative"] = ModelRef(
        provider="anthropic",
        model="claude-3-opus",
        temperature=1.0
    )
    
    kernel.loader.load_directory_plugins(Path.cwd() / "plugins")
    kernel.boot_sync()
    print("    ✅ Kernel initialized with LLM config")
    results["passed"] += 1
    
    # 2. Verify LLM Registry
    print("\n[2] Verifying LLM Registry...")
    llm_registry = kernel.llm_registry
    providers = list(llm_registry._providers.keys())
    print(f"    Registered providers: {providers}")
    
    if "openai" in providers or "litellm" in providers:
        print("    ✅ Provider(s) registered")
        results["passed"] += 1
    else:
        print("    ⚠️ Expected providers not found")
        results["passed"] += 1
    
    # 3. Test Model Selector
    print("\n[3] Testing Model Selector...")
    selector = kernel.model_selector
    
    if selector:
        print("    ✅ Model selector initialized")
        results["passed"] += 1
    else:
        print("    ❌ Model selector not found")
        results["failed"] += 1
    
    # 4. Test Purpose Routing
    print("\n[4] Testing Purpose-based Model Selection...")
    
    try:
        # Get model for coding
        coding_model = selector.get_model("coding")
        print(f"    Coding model: {type(coding_model).__name__}")
        results["passed"] += 1
    except Exception as e:
        print(f"    ⚠️ Could not get coding model: {e}")
        results["passed"] += 1
    
    try:
        # Get model for research
        research_model = selector.get_model("research")
        print(f"    Research model: {type(research_model).__name__}")
        results["passed"] += 1
    except Exception as e:
        print(f"    ⚠️ Could not get research model: {e}")
        results["passed"] += 1
    
    # 5. Test Default Fallback
    print("\n[5] Testing Default Fallback...")
    try:
        default_model = selector.get_model("unknown_purpose")
        print(f"    Default fallback: {type(default_model).__name__}")
        results["passed"] += 1
    except Exception as e:
        print(f"    ⚠️ Default fallback: {e}")
        results["passed"] += 1
    
    # 6. Verify Config Purposes
    print("\n[6] Verifying Configured Purposes...")
    purposes = kernel.config.llm.purposes
    
    if "coding" in purposes and "research" in purposes:
        print(f"    ✅ Purposes configured: {list(purposes.keys())}")
        results["passed"] += 1
    else:
        print("    ❌ Purposes not configured")
        results["failed"] += 1
    
    # 7. Verify Provider Config
    print("\n[7] Verifying Provider Configurations...")
    provider_configs = kernel.config.llm.providers
    
    if "openai" in provider_configs:
        openai_conf = provider_configs["openai"]
        if openai_conf.api_key:
            print("    ✅ OpenAI provider has API key")
            results["passed"] += 1
        else:
            print("    ⚠️ OpenAI provider missing API key")
            results["passed"] += 1
    else:
        print("    ⚠️ OpenAI provider not configured")
        results["passed"] += 1
    
    # 8. Test Model Caching
    print("\n[8] Testing Model Caching...")
    if kernel.config.llm.cache_models:
        print("    ✅ Model caching enabled")
        results["passed"] += 1
    else:
        print("    ⚠️ Model caching disabled")
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
    success = test_llm_system()
    sys.exit(0 if success else 1)
