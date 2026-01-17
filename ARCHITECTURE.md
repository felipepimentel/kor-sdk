# KOR: Enterprise Developer Platform - Technical Blueprint

**Version:** 6.0 (Plugin-First Architecture)
**Target:** AI Engineering Assistants
**Core Philosophy:** "Everything is a Plugin."

## 1. High-Level Architecture

The system is split into three distinct layers:

1. **The SDK (`kor-core`)**: The shared library containing business logic, event bus, and types.
2. **The CLI (`kor-cli`)**: A thin entry point (`kor`) responsible ONLY for plugin management and command dispatching.
3. **The Plugins (`plugins/*`)**: All functionality, including the UI, lives here.

### Workspace Structure

```text
/kor-monorepo
├── pyproject.toml
├── uv.lock
├── packages/
│   ├── kor-core/           # SDK (Library)
│   └── kor-cli/            # CLI Entrypoint (kor)
│       └── Role: Dispatches 'kor <cmd>' to plugins.
│
└── plugins/
    ├── kor-plugin-tui/     # The TUI (Shifted from packages/)
    └── kor-plugin-system/  # System Info
```

## 2. Command Dispatching Strategy

The `kor` CLI works as a dynamic dispatcher.

* `kor plugins install <name>`: Adds a plugin to the environment.
* `kor <command>`:
    1. Scans installed plugins for `command` capability.
    2. Executes the plugin via `uv run`.

**Example:**
User types: `kor tui`

1. CLI checks plugins. Finds `kor-plugin-tui` registers `tui`.
2. CLI executes: `uv run --package kor-plugin-tui python -m kor_plugin_tui.main`

## 3. Package Specification: `kor-cli`

* **Entry Point:** `kor`
* **Tech:** Typer
* **Logic:**
  * Does NOT contain business logic.
  * Uses `kor-core` only for shared utilities (like `UVManager`).

## 4. Package Specification: `kor-plugin-tui`

* **Type:** Plugin.
* **Role:** Provides the "Default" UI.
* **Independence:** Can be swapped for `kor-plugin-web-ui` or `kor-plugin-voice`.

---

## 5. Migration Plan (v5 -> v6)

1. **Move** `packages/kor-tui` -> `plugins/kor-plugin-tui`.
2. **Create** `packages/kor-cli`.
3. **Implement** the Dispatcher logic in `kor-cli`.
