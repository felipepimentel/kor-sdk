import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from kor_core import GraphRunner

console = Console()

@click.command()
def chat():
    """Starts the interactive KOR agent session."""
    console.print(Panel("Starting KOR Agent (LangGraph/Supervisor Mode)", style="bold purple"))
    
    runner = GraphRunner()

    while True:
        try:
            user_input = console.input("[bold cyan]You > [/]")
            if user_input.lower() in ("exit", "quit"):
                break
                
            console.print("[dim]Thinking...[/dim]")
            
            # Streaming events from the graph
            for event in runner.run(user_input):
                for node, details in event.items():
                    # Format output based on node type
                    if node == "Supervisor":
                        next_step = details.get("next_step", "Unknown")
                        color = "yellow" if next_step != "FINISH" else "green"
                        console.print(f"[bold {color}]Supervisor[/]: Routing to -> {next_step}")
                    
                    elif node in ["Coder", "Researcher"]:
                        messages = details.get("messages", [])
                        for msg in messages:
                            content = getattr(msg, "content", str(msg))
                            console.print(Panel(Text(content), title=f"[bold blue]{node}[/]", border_style="blue"))
                            
        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

    console.print("[bold purple]Goodbye![/]")
