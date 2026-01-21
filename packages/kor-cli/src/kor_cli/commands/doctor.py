import click
import sys
import subprocess
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

@click.command()
def doctor():
    """Runs diagnostics to ensure KOR is healthy."""
    console.print("[bold blue]KOR Diagnostic Tool[/]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Component", style="dim")
    table.add_column("Status")
    table.add_column("Details")

    # 1. Python version
    py_version = sys.version.split()[0]
    table.add_row("Python", "[green]✔[/]", py_version)

    # 2. Kernel Boot
    try:
        from kor_core.kernel import get_kernel
        kernel = get_kernel()
        kernel.boot_sync()
        table.add_row("KOR Kernel", "[green]✔[/]", "Booted successfully")
        
        # 2.1 Registry check
        tools_registry = kernel.registry.get_service("tools")
        tool_count = len(tools_registry.get_all()) if tools_registry else 0
        table.add_row("Tool Registry", "[green]✔[/]", f"{tool_count} tools registered")
        
        agent_registry = kernel.registry.get_service("agents")
        agent_count = len(agent_registry.list_agents()) if agent_registry else 0
        table.add_row("Agent Registry", "[green]✔[/]", f"{agent_count} agents available")
        
    except Exception as e:
        table.add_row("KOR Kernel", "[red]✘[/]", f"Boot failed: {e}")

    # 3. Config & AI Check
    config_path = Path.home() / ".kor" / "config.toml"
    if config_path.exists():
        table.add_row("Config", "[green]✔[/]", f"Found at {config_path}")
        
        # Check LLM Status
        try:
            from kor_core.config import ConfigManager
            cfg = ConfigManager(config_path=config_path).load()
            if cfg.llm.default:
                provider_info = f"{cfg.llm.default.provider}:{cfg.llm.default.model}"
                table.add_row("Active AI", "[green]✔[/]", f"Using {provider_info}")
            else:
                 table.add_row("Active AI", "[yellow]![/]", "No default LLM configured")
        except Exception:
             table.add_row("Active AI", "[red]✘[/]", "Failed to load config")
            
    else:
        table.add_row("Config", "[yellow]![/]", "Not found (default will be created)")

    # 4. Global Tools
    tools = [
        ("uv", ["uv", "--version"]),
        ("git", ["git", "--version"]),
    ]
    
    for name, cmd in tools:
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                table.add_row(name, "[green]✔[/]", res.stdout.strip())
            else:
                table.add_row(name, "[yellow]![/]", "Not found or error")
        except FileNotFoundError:
            table.add_row(name, "[yellow]![/]", "Not installed")

    console.print(table)
