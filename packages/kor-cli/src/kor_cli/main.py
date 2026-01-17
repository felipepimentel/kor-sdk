import logging
import time
import click
from rich.console import Console
from rich.panel import Panel
from rich.logging import RichHandler
from kor_core import Kernel, KorPlugin, KorContext
from .commands.chat import chat

# Configure logging to use Rich
logging.basicConfig(
    level=logging.INFO, 
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, markup=True)]
)
logger = logging.getLogger("kor")
console = Console()

# --- Simulation of a defined Plugin ---
class HelloWorldPlugin(KorPlugin):
    id = "hello-world"
    
    def initialize(self, context: KorContext):
        # logger.info(f"[[bold green]{self.id}[/]] Initialized! Dependency Injection works.")
        context.registry.register_service("greeter", self.greet)

    def greet(self, name: str):
        return f"Hello, {name} from KOR!"

@click.group()
def main():
    """KOR - The Developer Operating System"""
    pass

@main.command()
def boot():
    """Boots the Kernel and runs diagnostics."""
    console.print(Panel.fit("[bold blue]KOR[/] - The Developer Operating System", border_style="blue"))
    
    with console.status("[bold green]Booting Kernel...[/]", spinner="dots"):
        kernel = Kernel()
        kernel.loader.register_plugin_class(HelloWorldPlugin)
        kernel.boot()
        time.sleep(0.5)
    
    console.print(f"[bold]Session User:[/bold] {kernel.config.user.name or 'Guest'}")
    console.print("[bold green]✔ System Ready.[/]")

# Add subcommands
main.add_command(chat)

if __name__ == "__main__":
    main()
