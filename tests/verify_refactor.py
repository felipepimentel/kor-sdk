"""
Verify Configurable Model Refactor.
"""
from kor_core.config import ConfigManager
from kor_core.agent.nodes import get_model

def test_config_model():
    cm = ConfigManager()
    
    # 1. Save original config
    original_model = cm.config.model.name
    
    try:
        # 2. Set new model and dummy key
        print(f"Original model: {original_model}")
        cm.set("model.name", "gpt-3.5-turbo-test")
        cm.set("secrets.openai_api_key", "sk-dummy-key")
        
        # 3. Get LLM via factory
        llm = get_model()
        
        print(f"Loaded LLM model: {llm.model_name}")
        
        # 4. Assert
        if llm.model_name == "gpt-3.5-turbo-test":
            print("SUCCESS: OpenAI model config is respected.")
        else:
            print(f"FAILURE: Expected gpt-3.5-turbo-test, got {llm.model_name}")

        # 5. Test Anthropic
        cm.set("model.provider", "anthropic")
        cm.set("model.name", "claude-3-haiku-test")
        cm.set("secrets.anthropic_api_key", "sk-ant-dummy")
        
        llm_ant = get_model()
        print(f"Loaded Anthropic model: {llm_ant.model}") # Anthropic uses .model instead of .model_name in some versions
        
        if llm_ant.model == "claude-3-haiku-test":
            print("SUCCESS: Anthropic model config is respected.")
        else:
            print(f"FAILURE: Expected claude-3-haiku-test, got {llm_ant.model}")
            
    finally:
        # Restore
        cm.set("model.provider", "openai")
        cm.set("model.name", original_model)
        print("Restored original config.")

if __name__ == "__main__":
    test_config_model()
