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
            print("SUCCESS: Model config is respected.")
        else:
            print(f"FAILURE: Expected gpt-3.5-turbo-test, got {llm.model_name}")
            
    finally:
        # 5. Restore
        cm.set("model.name", original_model)
        print("Restored original config.")

if __name__ == "__main__":
    test_config_model()
