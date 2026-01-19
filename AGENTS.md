# AGENTS.md - KOR SDK Context & Guide

> **Context File for AI Agents**
> This file describes the KOR SDK project structure, architecture, and workflows to help you understand and contribute effectively.

## 1. Project Overview

**KOR SDK** is a modular, plugin-first Python framework for building advanced AI agents. It provides a robust kernel, dynamic agent orchestration, and extensible tool/LLM layers.

- **Primary Language**: Python 3.12+ (managed via `uv`)
- **Core Philosophy**: "Everything is a Plugin". The core is minimal; capabilities are added via plugins.
- **Key Dependencies**: `langgraph`, `langchain`, `pydantic`.

## 2. Architecture

The system is built around a **Pythonic Facade** (`Kor`) and a **Singleton Kernel** that orchestrates services.

### Core Components

1. **Facade** (`kor_core.api.Kor`): The primary entry point for developers. Provides a fluent API for booting, configuring, and running agents.
2. **Kernel** (`kor_core.kernel`): The central orchestrator. Bootstraps the system, loads plugins, and exposes the Service Registry.
3. **Service Registry**: A dependency injection container. Holds `agents`, `tools`, `llm`, `skills`.
4. **Vertical Modules**: Core subsystems are organized vertically:
    - `kor_core.mcp`: Model Context Protocol (Client & Server)
    - `kor_core.lsp`: Language Server Protocol (Validation & Intelligence)
    - `kor_core.skills`: Skills Registry & Discovery
    - `kor_core.llm`: LLM Providers & Selection

### The Three Layers of Extensibility

1. **LLM Layer** (`kor-core/llm`):
    - **Unified Provider**: Single usage pattern for OpenAI, Anthropic, Local (Ollama/LM Studio).
    - **Selector**: Routes requests based on "Purpose" (e.g., `research` -> Perplexity).
2. **Agent Layer** (`kor-core/agent`):
    - **Unified Definition**: Single `AgentDefinition` for both declarative and code-based agents.
    - **State Graph**: Based on LangGraph.
3. **Tooling Layer** (`kor-core/tools`):
    - **Registry**: Central repository of tools.
    - **Discovery**: Agents search for tools by semantic tags.

## 3. Directory Map

The codebase follows a **Vertical Architecture** with consolidated modules:

- `packages/kor-core/src/kor_core/`:
  - `api.py`: **Main Entry Point** (Kor Facade).
  - `kernel.py`: Core orchestrator.
  - `plugin.py`: Plugin System (Loader, Manifest, Context).
  - `skills.py`: Skill System (Registry, Loader).
  - `prompts.py`: Prompt Loading logic.
  - `events.py`: Unified Event Bus.
  - `search.py`: Unified Search Backend.
  - `commands.py`: Unified Command System.
  - `config.py`: Configuration & Environment.
  - `utils.py`: Shared utilities.
  - `mcp/`: Model Context Protocol.
  - `lsp/`: Language Server Protocol.
  - `tools/`: Tool Implementations.
  - `llm/`: LLM Subsystem.
  - `agent/`: Agent Subsystem.
  - `resources/` (Repo Root): Non-code assets.

## 4. Architectural Principles

1. **Vertical Architecture**: Each domain is self-contained.
2. **Consolidated Code**: Related classes are in single files (`plugin.py`, `skills.py`, `events.py`) to reduce file hopping.
3. **Unified Abstractions**: Single `AgentDefinition`, single `BaseLoader`.
4. **Facade First**: Public API accessed via `Kor()` facade.
5. **Clean Root**: Resource files moved to repository root `resources/`.

## 5. Common Workflows

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

## 6. Recommended Agent Protocol

1. **Search First**: When asked about "Auth", do NOT `cat auth.py`. Use `search_symbols("Auth")` to find the exact file and class.
2. **Edit Safely**: Do NOT use `write_to_file` for partial code logic. Use `smart_edit` which guarantees syntax correctness.
3. **Check Task**: Always verify `task.md` for current progress.
