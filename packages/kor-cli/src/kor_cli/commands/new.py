import click
import os
import json
from pathlib import Path
from rich.console import Console

console = Console()

@click.command()
@click.argument('name')
@click.option('--plugin', is_flag=True, default=True, help="Create a plugin scaffold (default)")
def new(name: str, plugin: bool):
    """Scaffolds a new KOR project or plugin."""
    target_dir = Path(os.getcwd()) / name
    
    if target_dir.exists():
        console.print(f"[bold red]Error:[/] Directory '{name}' already exists.")
        return

    console.print(f"Creating [bold cyan]{name}[/]...")
    target_dir.mkdir(parents=True)

    if plugin:
        _scaffold_plugin(target_dir, name)
    
    console.print(f"[bold green]Success![/] New plugin scaffolded at {target_dir}")
    
    console.print("\n[bold]Next Steps:[/]")
    console.print("1. Link your plugin:")
    console.print(f"   [cyan]ln -s {target_dir} ~/.kor/plugins/{name}[/]")
    console.print("2. Boot KOR:")
    console.print("   [cyan]kor boot[/]")
    console.print("3. Check it loaded:")
    console.print("   [cyan]kor doctor[/]")

def _scaffold_plugin(path: Path, name: str):
    # 1. Create plugin.json
    manifest = {
        "name": name,
        "version": "0.1.0",
        "description": f"New plugin: {name}",
        "entry_point": "main.py",
        "permissions": [],
        "commands_dir": "commands",
        "agents_dir": "agents",
        "skills_dir": "skills"
    }
    
    with open(path / "plugin.json", "w") as f:
        json.dump(manifest, f, indent=4)

    # 2. Create subdirectories
    (path / "commands").mkdir()
    (path / "agents").mkdir()
    (path / "skills").mkdir()

    # 3. Create main.py (Entry point)
    main_py_content = f"""from kor_core import KorPlugin, KorContext

class {name.replace('-', '_').capitalize()}Plugin(KorPlugin):
    id = "{name}"
    
    def initialize(self, context: KorContext):
        print(f"[{name}] Initialized!")
        # Register services or hooks here
"""
    with open(path / "main.py", "w") as f:
        f.write(main_py_content)
