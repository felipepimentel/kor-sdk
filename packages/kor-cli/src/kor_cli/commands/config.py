import click
from rich.console import Console
from kor_core import ConfigManager

console = Console()

@click.group()
def config():
    """Manage KOR configuration."""
    pass

@config.command("set")
@click.argument("key_value")
def config_set(key_value: str):
    """Set a configuration value (e.g., kor config set openai_api_key=sk-...)."""
    if "=" not in key_value:
        console.print("[red]Error:[/] Format must be KEY=VALUE")
        return
    
    key, value = key_value.split("=", 1)
    manager = ConfigManager()
    manager.load()
    
    try:
        manager.set(key, value)
        # Mask secrets in output
        display_value = value[:4] + "..." if "key" in key.lower() else value
        console.print(f"[green]✔[/] Set [cyan]{key}[/] = {display_value}")
    except KeyError as e:
        console.print(f"[red]Error:[/] {e}")

@config.command("get")
@click.argument("key")
def config_get(key: str):
    """Get a configuration value."""
    manager = ConfigManager()
    manager.load()
    
    try:
        value = manager.get(key)
        # Mask secrets
        if value and "key" in key.lower():
            value = value[:4] + "..." + value[-4:] if len(value) > 8 else "****"
        console.print(f"[cyan]{key}[/] = {value}")
    except KeyError as e:
        console.print(f"[red]Error:[/] {e}")
