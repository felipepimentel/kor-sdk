---
name: system-info
description: Get information about the current system (OS, Python version, etc.)
tags: [system, info, diagnostics]
---

## Usage

Execute the system info script to get details about the running environment.

```bash
python3 "${KOR_PLUGIN_ROOT}/scripts/system_info.py"
```

## Options

- `--json`: Output in JSON format for programmatic use

## Output

Returns information about:

- Operating System
- Python version
- Platform details
- Architecture
- Hostname
