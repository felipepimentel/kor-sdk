# Core Concepts

This guide covers the internal architecture of KOR SDK, designed for plugin developers and power users.

## 1. The Kernel

The `Kernel` is the central orchestrator of the SDK. It is responsible for:

- Loading configuration.
- initializing the `ServiceRegistry`.
- Discovering and loading plugins.
- Managing the lifecycle (Boot, Shutdown).
- Emitting global events via `HookManager`.

```python
from kor_core.kernel import get_kernel

async def main():
    kernel = get_kernel()
    await kernel.boot()
    # ... use kernel ...
    await kernel.shutdown()
```

## 2. Service Registry

KOR uses a service locator pattern. The `Kernel.registry` holds references to all major services.

```python
# Accessing services
agent_registry = kernel.registry.get_service("agents")
tool_registry = kernel.registry.get_service("tools")
llm_registry = kernel.registry.get_service("llm")
```

### Generic Access

Most registries implement a generic `get(id)` method for consistent access.

```python
agent = agent_registry.get("my-agent")
tool = tool_registry.get("my-tool")
```

## 3. Plugins

Plugins are the building blocks of KOR. A plugin can define agents, tools, commands, and hooks.

### Structure

A minimal plugin requires a `plugin.json` manifest:

```json
{
    "name": "kor-plugin-my-feature",
    "version": "1.0.0",
    "description": "Adds a cool feature",
    "entry_point": "my_feature.plugin:MyPlugin",
    "commands_dir": "commands",
    "skills_dir": "skills",
    "hooks_path": "hooks.json"
}
```

### Python Entry Point (Optional)

If you need advanced logic (like registering Python tools), define a class inheriting from `KorPlugin`.

```python
from kor_core.plugin import KorPlugin, KorContext

class MyPlugin(KorPlugin):
    id = "my-feature"
    
    def initialize(self, context: KorContext):
        # Register tools, agents, etc.
        pass
```

### Declarative Features

You can add features without any Python code:

- **Commands**: Add markdown files to `commands/` folder.
- **Skills**: Add markdown skills to `skills/` folder.
- **Hooks**: Define event listeners in `hooks.json`.

## 4. Hooks & Events

The `HookManager` allows plugins to react to system events.

### Implemented Events (`HookEvent`)

- `ON_BOOT`: Kernel has finished initializing.
- `ON_SHUTDOWN`: Kernel is shutting down.
- `ON_AGENT_START`: An agent has started working.
- `ON_TOOL_START` / `ON_TOOL_END`: Tool execution lifecycle.

### Declarative Hooks (`hooks.json`)

```json
{
    "on_boot": [
        { "log": "System is ready!" },
        { "command": "python script.py" }
    ]
}
```

## 5. Tools

Tools are units of executable logic exposed to agents.

### Creating Tools

1. **Decorators** (Simplest):

   ```python
   from kor_core.tools import tool

   @tool("my_tool", "Description of what it does")
   def my_tool(arg1: str):
       return f"Result: {arg1}"
   ```

2. **BaseTool** (Advanced):
   Inherit from `KorTool` (which wraps LangChain's `BaseTool`).

### Registering Tools

```python
registry = context.get_tool_registry()
registry.register(my_tool)
```
