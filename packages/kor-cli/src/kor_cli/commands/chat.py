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

    # Themes & Styles
    STYLE_SUPERVISOR = "bold yellow"
    STYLE_SUPERVISOR_DONE = "bold green"
    STYLE_AGENT_TITLE = "bold blue"
    STYLE_AGENT_BORDER = "blue"
    STYLE_ERROR = "bold red"
    STYLE_SYSTEM = "bold purple"

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
    console.print(Panel(f"Starting KOR Agent: [bold]{active_agent_id}[/bold] (Persistent)", style=STYLE_SYSTEM))
    
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
        console.print(f"[{STYLE_ERROR}]Failed to load agent {active_agent_id}: {e}[/]")
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
                        # Dynamic rendering based on payload structure, not Node Name
                        
                        # Case A: Routing/Supervisor Event
                        if "next_step" in details:
                            next_step = details.get("next_step", "Unknown")
                            color = STYLE_SUPERVISOR if next_step != "FINISH" else STYLE_SUPERVISOR_DONE
                            console.print(f"[{color}]{node}[/]: Routing to -> {next_step}")
                        
                        # Case B: Agent Message Event
                        elif "messages" in details:
                            messages = details.get("messages", [])
                            for msg in messages:
                                content = getattr(msg, "content", str(msg))
                                console.print(Panel(Text(content), title=f"[{STYLE_AGENT_TITLE}]{node}[/]", border_style=STYLE_AGENT_BORDER))
                        
                        # Case C: Tool Output or other
                        elif "output" in details:
                             console.print(f"[dim]{node} output: {details['output'][:100]}...[/dim]")

                        # Fallback
                        else:
                             pass # console.print(f"[dim]Event from {node}[/dim]")
                                
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[{STYLE_ERROR}]Error:[/{STYLE_ERROR}] {e}")

        console.print(f"[{STYLE_SYSTEM}]Goodbye![/]")
    finally:
        kor.shutdown()
