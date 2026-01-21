
import asyncio
import logging
import sys
import os

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
# Add kor-core source to sys.path
sys.path.append(os.path.join(project_root, "packages", "kor-core", "src"))

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from kor_core.kernel import Kernel
from kor_core.config import KorConfig, PluginsConfig

async def main():
    logger.info("Starting Verification Script for Virtual LLM...")

    # 1. Configure Kernel to load our new plugin
    # We use extra_paths to point to where we created the plugin
    plugin_path = "/home/pimentel/Workspace/kor-sdk/plugins/kor-plugin-virtual-llm"
    
    config_overrides = {
        "plugins": {
            "extra_paths": [plugin_path]
        },
        # We need to configure the LLM usage to use our new provider
        "llm": {
            "default": {
                "provider": "virtual",
                "model": "mock-model"
            }
        }
    }

    async with Kernel(config_options=config_overrides) as kernel:
        logger.info("Kernel booted.")
        
        # 2. Check if provider is registered
        providers = kernel.llm_registry.list_providers()
        logger.info(f"Registered Providers: {providers}")
        
        if "virtual" not in providers:
            logger.error("FAILED: 'virtual' provider not found in registry!")
            return

        # 3. Instantiate Model
        try:
            # We explicitly ask for the virtual provider
            logger.info("Requesting model from 'virtual' provider...")
            model = kernel.llm_registry.get_model(
                provider_name="virtual", 
                model_name="mock-model", 
                config={"default_response": "Verified Response from Script!"}
            )
            
            # 4. Invoke Model
            logger.info("Invoking model...")
            result = await model.ainvoke("Hello?")
            logger.info(f"Result content: {result.content}")
            
            expected = "Verified Response from Script!"
            if result.content == expected:
                logger.info("SUCCESS: Virtual LLM returned expected response.")
            else:
                logger.error(f"FAILED: Expected '{expected}', got '{result.content}'")

        except Exception as e:
            logger.exception("Error during model invocation:")

if __name__ == "__main__":
    asyncio.run(main())
