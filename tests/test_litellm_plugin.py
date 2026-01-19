import sys
from pathlib import Path
import os
import logging

# Add package source to path
sys.path.insert(0, str(Path.cwd() / "packages/kor-core/src"))
sys.path.insert(0, str(Path.cwd() / "plugins/kor-plugin-llm-litellm/src"))

from kor_core.kernel import get_kernel
from kor_core.config import ModelRef, ProviderConfig

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def test_litellm():
    print("--- Verifying LiteLLM Plugin Flexibility ---")
    
    # 1. Initialize Kernel
    kernel = get_kernel()
    
    # 2. Configure LiteLLM
    # In a real scenario, these keys would come from Env Vars or Config File
    # For this verification, we inject them into the config object.
    
    print("[1] Configuring LiteLLM Provider...")
    # API keys should be set in environment variables
    # Inject fake keys for testing registration logic
    os.environ["OPENROUTER_API_KEY"] = "sk-fake-openrouter"
    os.environ["PERPLEXITYAI_API_KEY"] = "sk-fake-perplexity"

    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    perplexity_key = os.environ.get("PERPLEXITYAI_API_KEY", "")
    
    if not openrouter_key or not perplexity_key:
        print("⚠️ SKIP: OPENROUTER_API_KEY and/or PERPLEXITYAI_API_KEY not set in environment")
        print("   Set these environment variables to run this verification test.")
        return
    
    # We configure a single "litellm" provider. 
    # LiteLLM usually reads env vars, but we can pass keys via 'extra' or specific fields if helpful.
    # However, LiteLLM expects keys in ENV vars for different providers usually.
    # OR we can pass it in 'api_key' if we are only using one.
    # BUT here we want MULTIPLE providers through ONE plugin.
    # So the best way is to set ENV vars for them.
    
    os.environ["OPENROUTER_API_KEY"] = openrouter_key
    os.environ["PERPLEXITYAI_API_KEY"] = perplexity_key
    
    # We register the provider config (even if empty, needed to enable it)
    kernel.config.llm.providers["litellm"] = ProviderConfig()
    
    # 3. Configure Purposes (Routing)
    print("[2] Setting up Purposes...")
    
    # Purpose 1: 'creative' -> OpenRouter (Gemini Pro 1.5)
    # LiteLLM format for openrouter: openrouter/google/gemini-2.0-flash-exp:free (or similar)
    # Let's use a standard one: openrouter/google/gemini-pro-1.5
    kernel.config.llm.purposes["creative"] = ModelRef(
        provider="litellm", 
        model="openrouter/google/gemini-2.0-flash-exp:free",
        temperature=0.9
    )
    
    # Purpose 2: 'research' -> Perplexity (Llama 3)
    # LiteLLM format: perplexity/llama-3-sonar-large-32k-online
    kernel.config.llm.purposes["research"] = ModelRef(
        provider="litellm", 
        model="perplexity/llama-3.1-sonar-small-128k-online",
        temperature=0.1
    )
    
    # 4. Boot Kernel (Load Plugins)
    print("[3] Loading Plugins & Booting...")
    # Load from workspace
    kernel.loader.load_directory_plugins(Path.cwd() / "plugins")
    kernel.boot_sync()
    
    # 5. Verify Registry
    registry = kernel.registry.get_service("llm")
    if "litellm" in registry.list_providers():
        print("✅ LiteLLM Provider Registered.")
    else:
        print("❌ FAIL: LiteLLM Provider NOT registered.")
        return

    # 6. Test Model Instantiation (Creative / OpenRouter)
    print("[4] Testing OpenRouter Instantiation (Creative)...")
    try:
        model = kernel.model_selector.get_model("creative")
        print(f"    Selected Class: {type(model).__name__}")
        print(f"    Model Name: {model.model_name}")
        # ChatLiteLLM properties
        # In newer langchain-community, it might store 'model' in .model_name or .model
        pass
    except Exception as e:
        print(f"❌ FAIL: OpenRouter instantiation failed: {e}")

    # 7. Test Model Instantiation (Research / Perplexity)
    print("[5] Testing Perplexity Instantiation (Research)...")
    try:
        model = kernel.model_selector.get_model("research")
        print(f"    Selected Class: {type(model).__name__}")
        print(f"    Model Name: {model.model_name}")
    except Exception as e:
        print(f"❌ FAIL: Perplexity instantiation failed: {e}")

    print("\n✅ Verification Complete.")

if __name__ == "__main__":
    verify_litellm()
