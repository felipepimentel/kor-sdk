import sys
import os
from pathlib import Path

# Add package source to path
sys.path.insert(0, str(Path.cwd() / "packages/kor-core/src"))
sys.path.insert(0, str(Path.cwd() / "plugins/kor-plugin-llm-openai/src"))

from kor_core.kernel import Kernel, get_kernel
from kor_core.config import LLMConfig, ProviderConfig, ModelRef
# Provider moved to core
from kor_core.llm.providers.openai import OpenAIProvider
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def test_llm_architecture():
    print("--- Verifying LLM Architecture ---")
    
    # 1. Initialize Kernel
    print("[1] Initializing Kernel...")
    kernel = get_kernel()
    
    # 2. Mock Configuration (Simulate config.toml)
    print("[2] Configuring LLM settings...")
    # NOTE: modifying config directly for test
    kernel.config.llm.providers["openai"] = ProviderConfig(api_key="sk-test-key")
    kernel.config.llm.purposes["supervisor"] = ModelRef(provider="openai", model="gpt-4-turbo")
    kernel.config.llm.default = ModelRef(provider="openai", model="gpt-3.5-turbo")
    
    # 2.5 Load Plugins from Workspace (Dev Mode)
    print(f"[2.5] Loading plugins from {Path.cwd() / 'plugins'}...")
    kernel.loader.load_directory_plugins(Path.cwd() / "plugins")

    # 3. Boot (loads plugins config)
    print("[3] Booting Kernel...")
    # Using sync wrapper for test script simplicity
    kernel.boot_sync()
    
    # 4. Check Registry
    print("[4] Checking Registry...")
    registry = kernel.registry.get_service("llm")
    providers = registry.list_providers()
    print(f"    Registered Providers: {providers}")
    
    if "openai" not in providers:
        print("❌ FAIL: OpenAI provider not registered.")
        return
        
    # 5. Test Model Selection (Purpose)
    print("[5] Testing Model Selection (Purpose: supervisor)...")
    try:
        model = kernel.model_selector.get_model("supervisor")
        print(f"    Selected Model: {type(model).__name__}")
        print(f"    Model Name: {model.model_name}")
        
        if model.model_name != "gpt-4-turbo":
             print(f"❌ FAIL: Expected gpt-4-turbo, got {model.model_name}")
             return
    except Exception as e:
        print(f"❌ FAIL: Selection failed: {e}")
        return

    # 6. Test Model Selection (Override)
    print("[6] Testing Model Selection (Override: openai:gpt-4o)...")
    try:
        model = kernel.model_selector.get_model(override="openai:gpt-4o")
        print(f"    Selected Model: {type(model).__name__}")
        print(f"    Model Name: {model.model_name}")
        
        if model.model_name != "gpt-4o":
             print(f"❌ FAIL: Expected gpt-4o, got {model.model_name}")
             return
    except Exception as e:
        print(f"❌ FAIL: Override failed: {e}")
        return

    # 7. Test Nodes Refactoring
    print("[7] Testing nodes.py integration...")
    print("[7] Testing nodes.py integration...")
    # Nodes rely on Kernel context now, so no direct get_model import.
    # We verify that getting a model via selector works (covered above).
    # But if we want to simulate what a node does:
    model_node = kernel.model_selector.get_model("supervisor")
    if model_node:
        print(f"    Nodes.get_model('supervisor') returned: {model_node.model_name}")
    else:
        print("❌ FAIL: Nodes.get_model returned None")
        return

    print("\n✅ SUCCESS: LLM Architecture Verified!")

if __name__ == "__main__":
    test_llm_architecture()
