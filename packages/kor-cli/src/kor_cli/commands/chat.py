import click
from typing import Any
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from kor_core import GraphRunner, Kernel
from kor_core.agent.persistence import get_sqlite_checkpointer
from kor_core.agent.graph import create_graph

console = Console()

@click.command()
def chat():
    """Starts the interactive KOR agent session."""
    
    # Boot Kernel to load plugins/agents
    from kor_core.kernel import get_kernel
    kernel = get_kernel()
    kernel.boot()

    # 2. Setup Permission Handler (HITL)
    def ask_permission(action: str, details: Any) -> bool:
        if action == "terminal_command":
            click.secho(f"\n[PERMISSION] Agent wants to run: {details}", fg="yellow", bold=True)
            return click.confirm("Allow execution?", default=False)
        return True

    kernel.permission_callback = ask_permission
    
    # 3. Setup Persistence
    checkpointer = get_sqlite_checkpointer()
    
    # Resolve active agent
    active_agent_id = kernel.config.agent.active
    console.print(Panel(f"Starting KOR Agent: [bold]{active_agent_id}[/bold] (Persistent)", style="bold purple"))
    
    try:
        agent_registry = kernel.registry.get_service("agents")
        # Load agent definition
        agent_def = agent_registry.get_agent_definition(active_agent_id)
        
        # We need a slightly more complex loading if it's the internal supervisor
        if active_agent_id == "default-supervisor":
             graph = create_graph(checkpointer=checkpointer)
        else:
             graph = agent_registry.load_graph(active_agent_id)
             # NOTE: External graphs might need to support checkpointer as well in their factory
             
        runner = GraphRunner(graph=graph)
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
                
                # Streaming events from the graph
                for event in runner.run(user_input, thread_id="main-session"):
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
        kernel.shutdown()
