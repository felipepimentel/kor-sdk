"""
Verify Configurable Model Refactor.
"""
from kor_core.config import ConfigManager
from kor_core.kernel import get_kernel

def test_config_model():
    cm = ConfigManager()
    
    # 1. Save original config
    # Ensure default is initialized for test
    if not cm.config.llm.default:
        from kor_core.config import ModelRef
        cm.config.llm.default = ModelRef(provider="openai", model="gpt-4")
        
    original_model = cm.config.llm.default.model
    
    try:
        # 2. Set new model and dummy key
        print(f"Original model: {original_model}")
        
        # We need to manually update the Pydantic object for deep nested fields 
        # because the simple .set() method in V1 doesn't handle creating nested objects well
        # or we just usage direct assignment for verification
        cm.config.llm.default.model = "gpt-3.5-turbo-test"
        cm.config.llm.providers["openai"] = {"api_key": "sk-dummy-key"}
        
        # 3. Get LLM via factory
        # Use Kernel ModelSelector
        kernel = get_kernel()
        kernel.boot_sync() # Ensure kernel is booted so model_selector is initialized
        llm = kernel.model_selector.get_model("default")
        
        print(f"Loaded LLM model: {llm.model_name}")
        
        # 4. Assert
        if llm.model_name == "gpt-3.5-turbo-test":
            print("SUCCESS: OpenAI model config is respected.")
        else:
            print(f"FAILURE: Expected gpt-3.5-turbo-test, got {llm.model_name}")

        # 5. Test Anthropic (Manual Config Update)
        cm.config.llm.default.provider = "anthropic"
        cm.config.llm.default.model = "claude-3-haiku-test"
        cm.config.llm.providers["anthropic"] = {"api_key": "sk-ant-dummy"}
        
        llm_ant = get_kernel().model_selector.get_model("default")
        try:
             # Anthropic uses .model or .model_name depending on version
             actual_model = getattr(llm_ant, "model", getattr(llm_ant, "model_name", "unknown"))
             print(f"Loaded Anthropic model: {actual_model}") 
        except:
             actual_model = "unknown"
        
        if actual_model == "claude-3-haiku-test":
            print("SUCCESS: Anthropic model config is respected.")
        else:
            print(f"FAILURE: Expected claude-3-haiku-test, got {actual_model}")
            
    finally:
        # Restore
        cm.config.llm.default.provider = "openai"
        cm.config.llm.default.model = original_model
        print("Restored original config.")

if __name__ == "__main__":
    test_config_model()
