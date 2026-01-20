# KOR Context Platform

The **Dynamic Context Acquisition Platform** allows agents to fetch context (docs, skills, data) from any source using a unified protocol.

## Core Concepts

### 1. Context Manager

The singleton orchestrator (`kor.context`) that resolves URIs to content.

### 2. Context URI

Standard format: `scheme://path?query` or `path` (defaults to `local://`)

- `local://readme.md`: Local file.
- `git://github.com/org/repo`: Git repository.
- `run:scripts/fetch_auth.py`: Output of a script.
- `skill://git`: Standard skill resolution (`.agent/skills/git/SKILL.md`).
- `mcp://github/README.md`: Resource from MCP server.
- `project:rules`: Auto-mapped to standard project locations.

### 3. Project Structure Standard (`.agent`)

KOR follows the emerging market standard for agent context:

```text
my-project/
├── .agent/              # Agent Context Directory
│   ├── AGENTS.md        # Master instruction file (Identity, High-level goals)
│   ├── rules.md         # Global rules and constraints
│   ├── memories/        # Project-specific long-term memories
│   ├── skills/          # Project-specific skills
│   │   └── git/
│   │       └── SKILL.md # Standard Skill Format
│   └── context/         # Additional docs (Architecture, PRDs)
│       ├── prd.md
│       └── design.md
├── src/
└── README.md
```

When KOR boots, it automatically detects `.agent/` and provides the following aliases (if files exist):

- `project:root` -> `local://.agent/`
- `project:agent` -> `local://.agent/AGENTS.md` (or `AGENT.md`)
- `project:rules` -> `local://.agent/rules.md`
- `project:memory` -> `local://.agent/memories/`
- `project:skills` -> `local://.agent/skills/`

### 4. Configuration

Configure mappings in `~/.kor/config.toml`:

```toml
[context.mapping]
"skill:*" = "git://github.com/my-team/skills"
"prd:login" = "run:scripts/fetch_prd.py --feature login"
```

## Usage for Developers

```python
from kor_core.context import get_context_manager

async def main():
    cm = get_context_manager()
    
    # 1. Direct Resolution (Local by default)
    result = await cm.resolve("README.md") 
    
    # 2. Standard Project Context
    # Automatically resolves to .agent/AGENTS.md if it exists
    context = await cm.resolve("project:agent")
```

## Agent Tools

KOR provides standard tools for agents to interact with the Context Platform.

### `GetContextTool`

Allows agents to fetch context by URI.

- **Name**: `get_context`
- **Input**: `uri` (e.g., `skill://git`, `project:rules`), `query` (optional)
- **Output**: Content of the resolved context.

## Extending

Create a plugin that registers a resolver:

```python
from kor_core.context import ContextResolverProtocol
class MyResolver(ContextResolverProtocol):
    async def resolve(self, uri, query):
        ...
```
