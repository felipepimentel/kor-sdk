import click
import subprocess
import sys
import importlib.metadata
from rich.console import Console
from rich.table import Table

console = Console()

@click.group()
def plugin():
    """Manage KOR plugins."""
    pass

@plugin.command()
@click.argument("package_name")
@click.option("--editable", "-e", is_flag=True, help="Install in editable mode")
def install(package_name, editable):
    """
    Install a plugin package.
    
    This wraps `uv pip install` (or falls back to `pip`) to install the plugin
    into the current environment.
    """
    cmd = [sys.executable, "-m", "pip", "install"]
    if editable:
        cmd.append("-e")
    cmd.append(package_name)
    
    try:
        # Try using uv if available for speed, otherwise standard pip
        # For now, let's stick to standard pip or uv pip if we were sure about environment
        # But sys.executable -m pip is the safest portable way for the current venv
        
        console.print(f"[bold blue]Installing plugin: {package_name}...[/]")
        subprocess.check_call(cmd)
        console.print(f"[bold green]Successfully installed {package_name}![/]")
        
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Failed to install plugin: {e}[/]")
        sys.exit(1)

@plugin.command()
def list():
    """List installed KOR plugins."""
    table = Table(title="Installed KOR Plugins")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Description")

    # Discover plugins via entry point 'kor.plugin'
    eps = importlib.metadata.entry_points(group="kor.plugin")
    
    if not eps:
        console.print("[yellow]No plugins found.[/]")
        return

    for ep in eps:
        try:
            dist = ep.dist
            name = dist.name if dist else ep.name
            version = dist.version if dist else "unknown"
            desc = list(dist.metadata.get_all("Summary") or [])[0] if dist else ""
            
            table.add_row(name, version, desc)
        except Exception:
            table.add_row(ep.name, "error", "Failed to load metadata")

    console.print(table)

@plugin.command()
@click.argument("package_name")
def uninstall(package_name):
    """Uninstall a plugin."""
    cmd = [sys.executable, "-m", "pip", "uninstall", "-y", package_name]
    
    try:
        console.print(f"[bold blue]Uninstalling {package_name}...[/]")
        subprocess.check_call(cmd)
        console.print(f"[bold green]Successfully uninstalled {package_name}.[/]")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Failed to uninstall plugin: {e}[/]")
        sys.exit(1)
