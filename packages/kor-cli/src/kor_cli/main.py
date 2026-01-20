import logging
import time
import click
from rich.console import Console
from rich.panel import Panel
from rich.logging import RichHandler
from kor_core import Kernel
from kor_core.events import HookManager
from .commands.chat import chat
from .commands.new import new
from .commands.doctor import doctor
from .commands.config import config
from .commands.serve import serve
from .commands.trace import trace
from .commands.plugin import plugin
from .commands.version import version

# Configure logging to use Rich
logging.basicConfig(
    level=logging.INFO, 
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, markup=True)]
)
logger = logging.getLogger("kor")
console = Console()

# Global hook manager for CLI events
cli_hooks = HookManager()

# ASCII Art Banner
KOR_BANNER = """
[bold blue]
██╗  ██╗ ██████╗ ██████╗ 
██║ ██╔╝██╔═══██╗██╔══██╗
█████╔╝ ██║   ██║██████╔╝
██╔═██╗ ██║   ██║██╔══██╗
██║  ██╗╚██████╔╝██║  ██║
╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝
[/bold blue][dim]The Developer Operating System[/dim]
"""

@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """KOR CLI - The Developer Operating System"""
    if ctx.invoked_subcommand is None:
        console.print(KOR_BANNER)
        console.print("[dim]Run [bold]kor --help[/bold] for available commands.[/dim]\n")

@main.command()
def boot():
    """Boots the Kernel and runs diagnostics."""
    console.print(Panel.fit("[bold blue]KOR[/] - The Developer Operating System", border_style="blue"))
    
    with console.status("[bold green]Booting Kernel...[/]", spinner="dots"):
        from kor_core import Kor
        kor = Kor()
        kor.boot()
        time.sleep(0.5)
    
    console.print(f"[bold]Session User:[/bold] {kor.config.user.name or 'Guest'}")
    console.print("[bold green]✔ System Ready.[/]")

# Add subcommands
main.add_command(chat)
main.add_command(new)
main.add_command(doctor)
main.add_command(config)
main.add_command(serve)
main.add_command(trace)
main.add_command(plugin)
main.add_command(version)

if __name__ == "__main__":
    main()
