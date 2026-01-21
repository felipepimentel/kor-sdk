import asyncio
from kor_core.kernel import Kernel

async def verify():
    print("Booting Kernel...")
    kernel = Kernel()
    await kernel.boot()
    
    print("Checking LLM Registry...")
    registry = kernel.registry.get_service("llm")
    providers = registry.list_providers()
    print(f"Registered Providers: {providers}")
    
    if "mock" in providers:
        print("[SUCCESS] MockProvider found.")
        
        # Test getting a model
        provider = registry.get_provider("mock")
        model = provider.get_chat_model("mock-gpt", {})
        resp = await model.ainvoke("Hello")
        print(f"Model Response: {resp.content}")
    else:
        print("[FAILURE] MockProvider NOT found.")

if __name__ == "__main__":
    asyncio.run(verify())
