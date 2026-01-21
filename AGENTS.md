# KOR SDK Context & Guide

> **Hello Agent!** 👋
> You are working on the **KOR SDK**, an advanced AI agent framework.
> This file is your primary orientation guide.

## 1. Golden Rules

1. **Respect Vertical Boundaries**: The code is organized into "Verticals" (e.g., `mcp/`, `lsp/`). Do not cross-import unless necessary.
2. **Use the Facade**: Always use `kor_core.Kor()` to interact with the system. Avoid internal APIs.
3. **Read Before Writing**: Use `grep_search` to find existing utilities. We have a unified `events.py`, `search.py`, and `config.py`. Do not reinvent them.
4. **Test Your Work**: Run `pytest` before declaring a task complete.

## 2. Architecture Quick Reference

* **Facade**: `packages/kor-core/src/kor_core/api.py` -> `class Kor`
* **Config**: `packages/kor-core/src/kor_core/config.py` -> `class KorConfig`
* **Kernel**: `packages/kor-core/src/kor_core/kernel.py`
* **Events**: `packages/kor-core/src/kor_core/events.py`

## 3. How to Gain Context

If you are asked to implement a feature, **load the relevant skill** first using `view_file`.

* **Understanding the Whole**: `.agent/skills/kor_context/SKILL.md` (Crucial architecture context)
* **Kanban App Integration**: `.agent/skills/kanban_dev/SKILL.md`

## 4. Common Tasks

### A. Creating a Plugin

Check `packages/kor-cli/src/kor_cli/commands/new.py` for the standard template.
Plugins should ideally be **Declarative** (`plugin.json` + `scripts/`) unless they need deep Python hooks.

### B. Adding a Tool

Tools are just Python functions wrapped with `@tool`.
They should be registered in the `ToolRegistry` via the `Kor` facade.

### C. Debugging

Use `kor doctor` to check the environment.
Use `kor dev` (if available) to run the development loop.

Good luck! 🚀
