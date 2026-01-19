#!/usr/bin/env python3
"""
System Information Tool Script

Standalone script that outputs system information.
Can be called directly or via hook command.
"""

import json
import platform
import sys
import os


def get_system_info() -> dict:
    """Gather comprehensive system information."""
    return {
        "os": f"{platform.system()} {platform.release()}",
        "python": sys.version.split()[0],
        "python_path": sys.executable,
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "hostname": platform.node(),
        "processor": platform.processor() or "Unknown",
    }


def main():
    """Main entry point - outputs JSON or formatted text."""
    info = get_system_info()
    
    # Check if JSON output is requested
    if "--json" in sys.argv:
        print(json.dumps(info, indent=2))
    else:
        # Human-readable format
        print(f"OS: {info['os']}")
        print(f"Python: {info['python']}")
        print(f"Platform: {info['platform']}")
        print(f"Architecture: {info['architecture']}")
        print(f"Hostname: {info['hostname']}")


if __name__ == "__main__":
    main()
