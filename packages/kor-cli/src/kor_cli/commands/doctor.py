import click
import sys
import platform
import subprocess
from pathlib import Path
from rich.console import Console
from rich.table import Table
from kor_core import Kernel

console = Console()

@click.command()
def doctor():
    """Runs diagnostics to ensure KOR is healthy."""
    console.print(f"[bold blue]KOR Diagnostic Tool[/]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Component", style="dim")
    table.add_column("Status")
    table.add_column("Details")

    # 1. Python version
    py_version = sys.version.split()[0]
    table.add_row("Python", "[green]✔[/]", py_version)

    # 2. Kernel Boot
    try:
        kernel = Kernel()
        kernel.boot()
        table.add_row("KOR Kernel", "[green]✔[/]", "Booted successfully")
    except Exception as e:
        table.add_row("KOR Kernel", "[red]✘[/]", f"Boot failed: {e}")

    # 3. Config Check
    config_path = Path.home() / ".kor" / "config.toml"
    if config_path.exists():
        table.add_row("Config", "[green]✔[/]", f"Found at {config_path}")
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
