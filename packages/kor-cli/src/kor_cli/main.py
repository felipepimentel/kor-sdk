import logging
import time
import asyncio
import click
from rich.console import Console
from rich.panel import Panel
from rich.logging import RichHandler
from kor_core import Kernel, KorPlugin, KorContext
from kor_core.events.hook import HookManager, HookEvent
from .commands.chat import chat
from .commands.new import new
from .commands.doctor import doctor
from .commands.config import config
from .commands.serve import serve
from .commands.trace import trace
from .commands.plugin import plugin

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

# --- Simulation of a defined Plugin ---
class HelloWorldPlugin(KorPlugin):
    id = "hello-world"
    
    def initialize(self, context: KorContext):
        context.registry.register_service("greeter", self.greet)

    def greet(self, name: str):
        return f"Hello, {name} from KOR!"

@click.group()
@click.pass_context
def main(ctx):
    """KOR - The Developer Operating System"""
    ctx.ensure_object(dict)
    ctx.obj['start_time'] = time.time()
    # Emit pre_command
    asyncio.get_event_loop().run_until_complete(cli_hooks.emit(HookEvent.PRE_COMMAND))

@main.result_callback()
@click.pass_context
def process_result(ctx, result):
    """Called after any command completes."""
    asyncio.get_event_loop().run_until_complete(cli_hooks.emit(HookEvent.POST_COMMAND))

@main.command()
def boot():
    """Boots the Kernel and runs diagnostics."""
    console.print(Panel.fit("[bold blue]KOR[/] - The Developer Operating System", border_style="blue"))
    
    with console.status("[bold green]Booting Kernel...[/]", spinner="dots"):
        kernel = Kernel()
        kernel.loader.register_plugin_class(HelloWorldPlugin)
        kernel.boot_sync()
        time.sleep(0.5)
    
    console.print(f"[bold]Session User:[/bold] {kernel.config.user.name or 'Guest'}")
    console.print("[bold green]✔ System Ready.[/]")

# Add subcommands
main.add_command(chat)
main.add_command(new)
main.add_command(doctor)
main.add_command(config)
main.add_command(serve)
main.add_command(serve)
main.add_command(trace)
main.add_command(plugin)

if __name__ == "__main__":
    main()
