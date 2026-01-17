from kor_core import AgentRuntime, EventBus, EventType, UVManager
import asyncio

async def main():
    print("Initializing Core...")
    bus = EventBus()
    agent = AgentRuntime(bus)
    
    # Verify Dynamic Discovery
    print("\n--- Verifying Plugin Discovery ---")
    plugins = await UVManager.list_plugins()
    print(f"Found plugins: {plugins}")
    assert "kor-plugin-system-info" in plugins, "Plugin not found dynamically!"
    print("Plugin discovery verified.\n")

    print("Simulating TUI Input: 'Please run the plugin'")
    
    # Subscribe a simple listener to print events
    class DebugListener:
        async def on_event(self, event):
            print(f"[EVENT] {event.type}: {event.payload}")
    
    bus.subscribe(DebugListener())

    async for token in agent.run_interaction("Please check system info using the plugin"):
        print(token, end="", flush=True)
    print("\n")

if __name__ == "__main__":
    asyncio.run(main())
