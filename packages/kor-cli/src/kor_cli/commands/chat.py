import click
from typing import Any
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from kor_core import GraphRunner
from kor_core.agent.persistence import get_checkpointer
from kor_core.agent.graph import create_graph

console = Console()

@click.command()
def chat():
    """Starts the interactive KOR agent session."""
    
    # 1. Boot Kor Facade
    from kor_core import Kor
    kor = Kor()
    kor.boot()

    # 2. Setup Permission Handler (HITL)
    def ask_permission(action: str, details: Any) -> bool:
        if action == "terminal_command":
            click.secho(f"\n[PERMISSION] Agent wants to run: {details}", fg="yellow", bold=True)
            return click.confirm("Allow execution?", default=False)
        return True

    # Access kernel via facade for advanced configuration
    kor.kernel.permission_callback = ask_permission
    
    # 3. Setup Persistence & Graph
    active_agent_id = kor.config.agent.active_graph
    console.print(Panel(f"Starting KOR Agent: [bold]{active_agent_id}[/bold] (Persistent)", style="bold purple"))
    
    try:
        # Check if we need to manually load a graph or if it's default
        graph = None
        
        # We need checkpointer for persistence
        from kor_core.agent.persistence import get_checkpointer
        checkpointer = get_checkpointer(kor.config.persistence)
        
        if active_agent_id == "default-supervisor":
             from kor_core.agent.graph import create_graph
             graph = create_graph(checkpointer=checkpointer)
        else:
             graph = kor.agents.load_graph(active_agent_id)
             # NOTE: External graphs might need to support checkpointer as well
             
        # We pass the graph to kor.run via force_graph
    except Exception as e:
        console.print(f"[bold red]Failed to load agent {active_agent_id}: {e}[/]")
        return

    try:
        while True:
            try:
                user_input = console.input("[bold cyan]You > [/]")
                if user_input.lower() in ("exit", "quit"):
                    break
                    
                console.print("[dim]Thinking...[/dim]")
                
                # Streaming events from the graph via Facade
                # Note: kor.run returns the generator from GraphRunner
                for event in kor.run(user_input, thread_id="main-session", force_graph=graph):
                    for node, details in event.items():
                        # Format output based on node type
                        if node == "Supervisor":
                            next_step = details.get("next_step", "Unknown")
                            color = "yellow" if next_step != "FINISH" else "green"
                            console.print(f"[bold {color}]Supervisor[/]: Routing to -> {next_step}")
                        
                        elif node in ["Coder", "Researcher", "Explorer"]:
                            messages = details.get("messages", [])
                            for msg in messages:
                                content = getattr(msg, "content", str(msg))
                                console.print(Panel(Text(content), title=f"[bold blue]{node}[/]", border_style="blue"))
                                
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")

        console.print("[bold purple]Goodbye![/]")
    finally:
        kor.shutdown()
