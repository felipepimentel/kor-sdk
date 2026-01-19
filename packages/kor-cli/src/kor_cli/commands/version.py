import click
from rich.console import Console
from rich.table import Table
import sys

console = Console()

@click.command()
def version():
    """Shows KOR SDK version and environment info."""
    from kor_core import __version__ as core_version
    
    console.print("[bold blue]KOR SDK[/] - AI Agent Framework\n")
    
    table = Table(show_header=False, box=None)
    table.add_column("Component", style="dim")
    table.add_column("Version")
    
    table.add_row("kor-core", core_version)
    table.add_row("Python", sys.version.split()[0])
    
    # Try to get CLI version
    try:
        from importlib.metadata import version as pkg_version
        cli_version = pkg_version("kor-cli")
        table.add_row("kor-cli", cli_version)
    except Exception:
        pass
    
    console.print(table)
