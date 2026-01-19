# KOR SDK Context & Guide

> **Primary Reference**:
>
> - **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md) (Read this for the source of truth on directory structure and design).
> - **Deep Context**: If you are an Antigravity agent, use the `kor_context` skill (`.agent/skills/kor_context/SKILL.md`) for deep understanding.

## 1. Project Overview

**KOR SDK** is a modular, plugin-first Python framework for building advanced AI agents.

- **Core Philosophy**: "Vertical Architecture" + "Pythonic Facade".
- **Stack**: Python 3.12+ (`uv`), LangGraph, Pydantic.

## 2. Quick Constraints & Rules

1. **Vertical Domain**: Respect the vertical boundaries (`mcp/`, `lsp/`, `skills/`). Do not cross-import unless necessary via public APIs.
2. **Facade Pattern**: Always use `kor_core.Kor()` to access the system. Do not import internal managers (`Kernel`, `HookManager`) directly in consumer code.
3. **Consolidated Modules**: If a module has < 5 files, prefer a single file (e.g., `events.py` instead of `events/__init__.py`).
4. **Resources**: Place non-code assets (prompts, schemas) in `resources/` at the repo root.

## 3. Common Workflows

### W1: Adding a Capability

Create a **Plugin**.

- **Declarative**: `plugin.json` + `scripts/` (Preferred for simple tools).
- **Python**: `kor_core/plugin.py` subclass (For deep integration).

### W2: Running Tests

```bash
uv run pytest tests/
```

(Maintain 100% pass rate. No regressions.)

### W3: CLI Development

The `kor` CLI uses the `Kor` facade.

- **Entry**: `packages/kor-cli/src/kor_cli/main.py`
- **Commands**: `packages/kor-cli/src/kor_cli/commands/`

## 4. Agent Protocol

1. **Search First**: Use `grep_search` or `find_by_name` to locate specific implementations.
2. **Read Context**: Use the `kor_context` skill to align with architectural decisions.
3. **Validate**: Always run `kor doctor` and `pytest` before declaring a task complete.
