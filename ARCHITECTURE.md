# KOR SDK Architecture

**Version:** 7.0 (Vertical Architecture)
**Core Philosophy:** "Consolidated, Pythonic, Vertical."

## 1. High-Level Overview

The KOR SDK is designed as a modular, vertical system where feature domains (like MCP, LSP, Skills) are self-contained. The system is exposed to developers through a high-level **Facade**.

### Layers

1. **Facade (`kor_core.api`)**: The polished surface. Users interact primarily with the `Kor` class.
2. **Kernel (`kor_core.kernel`)**: The internal engine. Orchestrates lifecycle, events (`HookManager`), and services.
3. **Vertical Modules**: Self-contained domains (`mcp`, `lsp`, `skills`, `plugin`) that encapsulate their own logic, loaders, and registries.
4. **Unified Utilities**: Shared infrastructure (`search`, `events`, `commands`, `utils`) used by all verticals.

## 2. Directory Structure

```text
packages/kor-core/src/kor_core/
├── api.py              # Public Entry Point (Facade)
├── kernel.py           # Core Orchestrator
├── events.py           # Unified Event Bus
├── search.py           # Unified Search Protocol
│
├── plugin.py           # Plugin System (Single File Module)
├── skills.py           # Skill System (Single File Module)
├── prompts.py          # Prompt System (Single File Module)
│
├── mcp/                # Model Context Protocol (Vertical)
├── lsp/                # Language Server Protocol (Vertical)
├── agent/              # Agent Logic (Vertical)
├── llm/                # LLM & Providers (Vertical)
└── tools/              # Tool Implementations (Shared)
```

## 3. Key Architectural Decisions

### Vertical Architecture

Instead of splitting code by technical layer (e.g., `loaders/`, `registries/`), we split by **domain**.

- **MCP** logic lives in `mcp/`.
- **LSP** logic lives in `lsp/`.
Makes the codebase easier to navigate and maintain.

### Consolidated Modules

For domains with low complexity (< 5 files), we consolidate classes into a single file to reduce file hopping.

- `plugin.py` contains `PluginLoader`, `PluginManifest`, `KorContext`.
- `skills.py` contains `SkillRegistry`, `SkillLoader`.

### Facade Pattern

We hide complexity behind the `Kor` facade.
**Before:** Users imported `Kernel`, `ToolRegistry`, `HookManager`.
**After:** Users just instantiate `Kor`.

```python
kor = Kor()
kor.boot()
kor.tools.register(...)
```

### Resource Isolation

Non-code assets (markdown prompts) are kept in `resources/` at the repository root, ensuring a clean separation from source code.

## 4. The Plugin System

KOR is designed to be extensible.

- **Core Plugins**: Loaded automatically from `kor_core`.
- **User Plugins**: Loaded from `~/.kor/plugins` or valid Python entry points.
- **Declarative Plugins**: Defined by `plugin.json` + `scripts/`, requiring no Python packaging.
