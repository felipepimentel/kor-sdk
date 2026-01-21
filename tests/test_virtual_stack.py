
import asyncio
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from kor_core.kernel import Kernel

async def main():
    logger.info("Starting Test Suite: Virtual Stack & Architecture Cleanup")

    # Plugin path
    plugin_path = "/home/pimentel/Workspace/kor-sdk/packages/kor-plugin-virtual-llm"
    
    config_overrides = {
        "plugins": {
            "extra_paths": [plugin_path]
        },
        "llm": {
            "default": {
                "provider": "virtual",
                "model": "mock-model"
            }
        }
    }

    async with Kernel(config_options=config_overrides) as kernel:
        logger.info("Kernel booted.")
        
        # TEST 1: Check Provider Registry Cleanliness
        providers = kernel.llm_registry.list_providers()
        logger.info(f"Registered Providers: {providers}")
        
        if "openai" in providers or "litellm" in providers:
            logger.error("FAILED: Legacy providers 'openai' or 'litellm' should NOT be registered by default.")
            return

        if "unified" not in providers:
             logger.error("FAILED: 'unified' provider MISSING.")
             return

        if "virtual" not in providers:
             logger.error("FAILED: 'virtual' provider MISSING.")
             return
             
        logger.info("TEST 1 PASSED: Registry is clean and correct.")

        # TEST 2: Programmable Mock (Triggers)
        try:
            logger.info("Testing Programmable Triggers...")
            
            # Configure a model with triggers
            model = kernel.llm_registry.get_model(
                provider_name="virtual", 
                model_name="mock-model", 
                config={
                    "default_response": "I don't know.",
                    "triggers": {
                        "hello": "Hi there!",
                        "status": "All systems go."
                    }
                }
            )
            
            # 2a. Trigger: hello
            res1 = await model.ainvoke("Well hello there friend.")
            if res1.content != "Hi there!":
                logger.error(f"FAILED: Expected 'Hi there!', got '{res1.content}'")
            else:
                 logger.info("  Trigger 'hello' -> PASSED")

            # 2b. Trigger: status
            res2 = await model.ainvoke("Report status please.")
            if res2.content != "All systems go.":
                logger.error(f"FAILED: Expected 'All systems go.', got '{res2.content}'")
            else:
                 logger.info("  Trigger 'status' -> PASSED")

            # 2c. Default
            res3 = await model.ainvoke("Random noise.")
            if res3.content != "I don't know.":
                 logger.error(f"FAILED: Expected 'I don't know.', got '{res3.content}'")
            else:
                 logger.info("  Default fallback -> PASSED")
                 
            logger.info("TEST 2 PASSED: Programmable triggers working.")

        except Exception as e:
            logger.exception("Error during programmable test:")

        # TEST 3: Queue Sequence
        try:
            logger.info("Testing Response Queue...")
             
            model_q = kernel.llm_registry.get_model(
                provider_name="virtual", 
                model_name="mock-model", 
                config={
                    "queue": ["First", "Second"]
                }
            )
            
            r1 = await model_q.ainvoke("1")
            r2 = await model_q.ainvoke("2")
            r3 = await model_q.ainvoke("3") # Should hit default
            
            if r1.content == "First" and r2.content == "Second" and r3.content == "Virtual Response":
                 logger.info("TEST 3 PASSED: Queue sequence working.")
            else:
                 logger.error(f"FAILED: Queue sequence mismatch. Got: {r1.content}, {r2.content}, {r3.content}")

        except Exception as e:
             logger.exception("Error during queue test:")

    logger.info("ALL TESTS COMPLETED.")

if __name__ == "__main__":
    asyncio.run(main())
