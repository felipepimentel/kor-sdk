# KOR — The Developer Operating System

> An extensible AI agent framework with a modular plugin architecture, inspired by Claude Code.
> **Status: Production Ready (v1.0)** 🚀

## ✨ Features

- **LangGraph Agent**: Supervisor-Worker pattern for task orchestration.
- **Optimized Kernel**: Asynchronous, lazy-loading singleton architecture.
- **Plugin System**: Manifest-based (`plugin.json`) with robust isolation.
- **Hooks**: Event-driven architecture (`on_boot`, `pre_command`) with telemetry.
- **MCP Support**: Model Context Protocol client for external tool integration.
- **Rich CLI**: Beautiful output with spinners, panels, and colors.

---

## 🚀 Quick Start

### 1. Install

```bash
# Clone the repository
git clone https://github.com/felipepimentel/kor-sdk.git
cd kor-sdk

# Install with uv
uv sync
```

### 2. Configure

```bash
# Set your API key (stored in ~/.kor/config.toml)
uv run kor config set openai_api_key=sk-your-key
```

### 3. Run

```bash
# Boot the system
uv run kor boot

# Start chatting with the agent
uv run kor chat

# Check system health
uv run kor doctor
```

### 4. Use in Python

```python
from kor_core import Kor

# Initialize
kor = Kor()
kor.boot()

# Use the facade
tools = kor.tools.search("file")
results = kor.run_sync("Analyze this code")
```

---

## 🛠️ CLI Commands

| Command | Description |
| --- | --- |
| `kor boot` | Initializes the Kernel and loads plugins. |
| `kor chat` | Starts an interactive session with the AI agent. |
| `kor doctor` | Runs diagnostics on your environment. |
| `kor new <name>` | Scaffolds a new plugin project. |
| `kor config set KEY=VALUE` | Sets a configuration value. |
| `kor config get KEY` | Gets a configuration value. |

---

## 🔌 Creating a Plugin

```bash
uv run kor new my-awesome-plugin
```

This generates:

```text
my-awesome-plugin/
├── agents/
├── commands/
├── skills/
├── main.py
└── plugin.json
```

Link your plugin to `~/.kor/plugins/` to activate it.

---

## 📄 License

MIT
