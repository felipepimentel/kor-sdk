# KOR SDK Developer Guide

Welcome to the KOR SDK Developer Guide. This document provides a high-level overview of the KOR architecture, its core components, and how to extend it through plugins and tools.

## Architecture Overview

KOR is designed as a modular, plugin-based SDK for building agentic AI applications. Its core philosophy is centered around a central **Kernel** that manages lifecycle, services, and discovery.

### Core Components

- **Kernel**: The central orchestrator. It manages the boot sequence, loads plugins, and provides access to core services like configuration and the tool registry.
- **ServiceRegistry**: A central hub where plugins can register and discover shared services.
- **Plugin System**: Allows extending the SDK with new LLM providers, tools, and custom logic.
- **Agent System**: A flexible framework based on LangGraph for building complex agentic behaviors.
- **LLM Selection**: A config-driven system for resolving which model to use for specific purposes.
- **Unified Search**: A shared infrastructure for semantic and keyword discovery of tools and skills.

---

## Getting Started

### Initializing the Kernel

The Kernel is the entry point for almost every KOR application. It can be initialized in both asynchronous and synchronous contexts.

```python
from kor_core import get_kernel

# Asynchronous boot (Preferred)
async def main():
    kernel = get_kernel()
    await kernel.boot()
    # Your code here...

# Synchronous boot
def script():
    kernel = get_kernel()
    kernel.boot_sync()
```

### Configuration

KOR uses a `config.toml` file (and environment variables) to manage settings. You can access the configuration through the Kernel:

```python
config = kernel.config
print(config.user.name)
```

---

## Extending KOR

### Creating Tools

You can create custom tools using the `@tool` decorator. Tools can optionally auto-register themselves with the Kernel.

```python
from kor_core.tools import tool

@tool(name="calculator", description="Performs basic math", auto_register=True, tags=["math"])
def calculator(a: int, b: int, op: str = "+") -> str:
    if op == "+": return str(a + b)
    return "Unknown operator"
```

### Creating Plugins

Plugins are classes that inherit from `KorPlugin`. They are initialized by the Kernel and can register services and tools.

```python
from kor_core import KorPlugin, KorContext

class MyPlugin(KorPlugin):
    @property
    def id(self) -> str:
        return "my-custom-plugin"

    def initialize(self, context: KorContext) -> None:
        # Register a tool or service
        context.registry.register_tool("custom_tool", lambda x: x)
```

### Plugin Discovery

Plugins can be discovered via:

1. **Entry Points**: Register your plugin class in `pyproject.toml` under `[project.entry-points.kor_plugins]`.
2. **Directory**: Place your plugin files in the `plugins/` directory of your workspace.

---

## Best Practices

- **Async First**: Favor the asynchronous API (`await kernel.boot()`) when possible.
- **Type Safety**: Use the typed version of `get_service[T]` to ensure type safety when retrieving shared capabilities.
- **Harden Connectivity**: Use the `is_alive()` check for MCP clients and other network-bound services.
- **Modular Nodes**: When building agents, keep your node functions modular and separated from the graph definition.

---

## Troubleshooting

- **Dependency Issues**: If LLM providers are missing, ensure you have installed the optional extras: `pip install kor-core[openai,anthropic]`.
- **Permission Errors**: If actions are denied, ensure you have set a `permission_callback` on the Kernel or disabled `paranoid_mode`.
- **Plugin Loading**: Run with `LOG_LEVEL=DEBUG` to see detailed plugin discovery logs.

---

## Declarative Plugins (Zero-Code)

KOR SDK supports **declarative plugins** that require no Python code. You can create full-featured plugins using only JSON, Markdown, and YAML files.

### Plugin Structure

```plaintext
my-plugin/
├── plugin.json              # Manifest (required)
├── commands/                # Slash commands as Markdown
│   └── deploy.md
├── agents/                  # Agent definitions
│   └── reviewer.md
├── skills/                  # Skills (SKILL.md files)
│   └── code-review/
│       └── SKILL.md
├── hooks.json               # Event handlers
├── .mcp.json                # MCP server configs
├── .lsp.json                # LSP server configs
└── src/                     # OPTIONAL: Python code
```

### Minimal Plugin (plugin.json only)

```json
{
    "name": "my-plugin",
    "version": "0.1.0",
    "description": "A simple declarative plugin"
}
```

That's it! No Python code required. The SDK auto-discovers resources.

---

### Slash Commands

Create markdown files in `commands/` with YAML frontmatter:

```markdown
---
name: deploy
description: Deploy the application
args: [environment, version]
---

## Steps

1. Build the project: `npm run build`
2. Push to registry
3. Notify team
```

---

### Declarative Agents

Define agents in `agents/` as markdown:

```markdown
---
id: code-reviewer
name: Code Reviewer
description: Reviews code for quality
skills: [code-review, best-practices]
tools: [read-file, search-symbols]
model: gpt-4o
---

## System Prompt

You are a senior code reviewer. Analyze code for quality,
security issues, and best practices.
```

---

### Hooks (hooks.json)

Declarative event handlers:

```json
{
  "on_agent_start": [
    {"log": {"message": "Agent {agent_id} starting...", "level": "info"}}
  ],
  "on_tool_call": [
    {"command": {"cmd": "echo 'Tool: {tool_name}'"}}
  ]
}
```

Supported actions: `log`, `emit_metric`, `command`, `set_context`

---

### MCP Configuration (.mcp.json)

```json
{
  "github": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}
  }
}
```

---

### LSP Configuration (.lsp.json)

```json
{
  "python": {
    "command": "pylsp",
    "extensionToLanguage": {".py": "python"}
  }
}
```

---

## Advanced: Python Plugins

For complex logic, add an `entry_point` to your manifest:

```json
{
    "name": "my-plugin",
    "version": "0.1.0",
    "description": "Plugin with custom Python logic",
    "entry_point": "my_plugin:MyPluginClass"
}
```

Then create `src/my_plugin/__init__.py`:

```python
from kor_core import KorPlugin, KorContext

class MyPluginClass(KorPlugin):
    @property
    def id(self) -> str:
        return "my-plugin"
    
    def initialize(self, context: KorContext) -> None:
        # Custom initialization
        pass
```
