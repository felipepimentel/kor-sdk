import logging
import time
from rich.console import Console
from rich.panel import Panel
from rich.logging import RichHandler
from kor_core import Kernel, KorPlugin, KorContext

# Configure logging to use Rich
logging.basicConfig(
    level=logging.INFO, 
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, markup=True)]
)
logger = logging.getLogger("kor")
console = Console()

# --- Simulation of a defined Plugin (usually in a separate file) ---
class HelloWorldPlugin(KorPlugin):
    id = "hello-world"
    
    def initialize(self, context: KorContext):
        # We can use the console from the context if we added it, or stick to logging
        logger.info(f"[[bold green]{self.id}[/]] Initialized! Dependency Injection works.")
        context.registry.register_service("greeter", self.greet)

    def greet(self, name: str):
        return f"Hello, {name} from KOR!"

class ConsumerPlugin(KorPlugin):
    id = "consumer"
    
    def initialize(self, context: KorContext):
        # Demonstrating dependency consumption
        try:
            greeter = context.registry.get_service("greeter")
            msg = greeter('Developer')
            logger.info(f"[[bold cyan]{self.id}[/]] Consuming service: [italic]{msg}[/]")
        except Exception as e:
            logger.error(f"[{self.id}] Failed to consume service: {e}")

def main():
    console.print(Panel.fit("[bold blue]KOR[/] - The Developer Operating System", border_style="blue"))
    
    with console.status("[bold green]Booting Kernel...[/]", spinner="dots"):
        # 1. Initialize Kernel (loads config automatically)
        kernel = Kernel()
        
        # 2. Manual Registration
        kernel.loader.register_plugin_class(HelloWorldPlugin)
        kernel.loader.register_plugin_class(ConsumerPlugin)
        
        # 3. Boot
        kernel.boot()
        time.sleep(1) # Fake delay to show spinner
    
    console.print(f"[bold]Session User:[/bold] {kernel.config.user.name or 'Guest'}")
    console.print("[bold green]✔ System Ready.[/]")

if __name__ == "__main__":
    main()
