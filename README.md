# KOR — The Developer Operating System

> An extensible AI agent framework with a modular plugin architecture, inspired by Claude Code.

## ✨ Features

- **LangGraph Agent**: Supervisor-Worker pattern for task orchestration.
- **Built-in Tools**: Terminal execution, Web search (DuckDuckGo).
- **Plugin System**: Manifest-based (`plugin.json`), with support for `commands/`, `agents/`, `skills/`.
- **Hooks**: Event-driven architecture (`on_boot`, `pre_command`).
- **MCP Support**: Model Context Protocol client for external tool integration.
- **Rich CLI**: Beautiful output with spinners, panels, and colors.

---

## 🚀 Quick Start

### 1. Install

```bash
# Clone the repository
git clone https://github.com/youruser/kor-sdk.git
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

---

## 🛠️ CLI Commands

| Command | Description |
|---|---|
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

```
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
