# AGENTS.md - KOR SDK Context & Guide

> **Context File for AI Agents**
> This file describes the KOR SDK project structure, architecture, and workflows to help you understand and contribute effectively.

## 1. Project Overview

**KOR SDK** is a modular, plugin-first Python framework for building advanced AI agents. It provides a robust kernel, dynamic agent orchestration, and extensible tool/LLM layers.

- **Primary Language**: Python 3.12+ (managed via `uv`)
- **Core Philosophy**: "Everything is a Plugin". The core is minimal; capabilities are added via plugins.
- **Key Dependencies**: `langgraph`, `langchain`, `pydantic`.

## 2. Architecture

The system is built around a **Singleton Kernel** that orchestrates services.

### Core Components

1. **Kernel** (`kor_core.kernel`): The central object. Bootstraps the system, loads plugins, and exposes the Service Registry.
2. **Service Registry**: A dependency injection container. Holds `agents`, `tools`, `llm`, `checkpointer`.
3. **Plugin System**:
    - **Manifest**: `plugin.json` defines metadata and entry points.
    - **Loader**: Discovers and initializes plugins.
    - **Interface**: `KorPlugin` (abstract base).

### The Three Layers of Extensibility

1. **LLM Layer** (`kor-core/llm`):
    - **Providers**: `kor-llm-openai`, `kor-llm-litellm`.
    - **Selector**: Routes requests based on "Purpose" (e.g., `research` -> Perplexity).
    - **Caching**: Unified model caching via `LLMRegistry`.
2. **Agent Layer** (`kor-core/agent`):
    - **Factory**: Creates LangGraph nodes from `config.toml` (Centralized Config).
    - **Supervisor**: Hub-and-spoke orchestration with dynamic member lists.
3. **Tooling Layer** (`kor-core/tools`):
    - **Registry**: Central repository of tools.
    - **Discovery**: Agents search for tools by semantic tags.

## 3. Directory Map

- `packages/kor-core`: The SDK core logic.
  - `src/kor_core/kernel.py`: Main entry point (Singleton).
  - `src/kor_core/agent/`: Graph, Factory, Persistence.
  - `src/kor_core/loader.py`: Plugin discovery.
  - `src/kor_core/config.py`: Configuration schemas.
- `plugins/`: First-party plugins.
  - `kor-plugin-llm-*`: LLM Providers.
  - `kor-plugin-openai-api`: REST API adapter.
- `tests/`: Integration verification (pytest).

## 4. Common Workflows

### W1: Adding a New Capability (Plugin)

1. Create `plugins/kor-plugin-myfeature`.
2. Define `plugin.json` with unique name and entry point.
3. Implement `KorPlugin` subclass in `__init__.py` or `plugin.py`.
4. Implement `initialize(context)` to register services or tools.

### W2: Configuring a New Agent

Edit `config.toml` (or `~/.kor/config.toml`):

```toml
[agent.definitions.MyAgent]
role = "Expert in..."
goal = "Solve..."
tools = ["terminal"]
supervisor_members = ["Coder", "MyAgent"]
```

### W3: Running Verification

Always run the full test suite after changes:

```bash
uv run pytest tests/
```

## 5. Code Standards

- **Type Hinting**: Mandatory for all public APIs.
- **Error Handling**: Use distinct exceptions (`ConfigurationError`, `PluginError`).
- **Imports**: Absolute imports within `kor_core`.
- **Config**: Do not hardcode values. Use `config.py` schemas.

## 6. Current State (Jan 2026)

- **Status**: Stable / Production Ready.
- **Audit**: Deep code cleanup completed (legacy files removed).
- **Architecture**: Lazy loading implemented for all plugins.
- **Deep Coding**:
  - `kor-plugin-smart-edit`: Verified file modifications.
  - `kor-plugin-code-graph`: Semantic code search.

## 7. Recommended Agent Protocol

1. **Search First**: When asked about "Auth", do NOT `cat auth.py`. Use `search_symbols("Auth")` to find the exact file and class.
2. **Edit Safely**: Do NOT use `write_to_file` for partial code logic. Use `smart_edit` which guarantees syntax correctness.
