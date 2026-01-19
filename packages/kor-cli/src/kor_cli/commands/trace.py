import json
import click
from pathlib import Path
from rich.console import Console
from rich.tree import Tree
from datetime import datetime

console = Console()

@click.command()
@click.option("--last", default=10, help="Number of last sessions to show")
@click.option("--all", "show_all", is_flag=True, help="Show all events")
def trace(last, show_all):
    """Visualizes agent execution trace."""
    trace_file = Path.home() / ".kor" / "telemetry" / "trace.jsonl"
    
    if not trace_file.exists():
        console.print("[red]No telemetry trace found.[/red]")
        return
        
    events = []
    with open(trace_file, "r") as f:
        for line in f:
            try:
                events.append(json.loads(line))
            except:
                pass
                
    if not events:
        console.print("[yellow]Empty trace log.[/yellow]")
        return

    # Group into "Runs" (each run starts with on_agent_start or on_boot)
    runs = []
    current_run = None
    
    for ev in events:
        # For our simple grouping, let's say on_agent_start marks a new block
        if ev['event'] == "on_agent_start":
            if current_run: runs.append(current_run)
            current_run = {"type": "Agent", "events": [ev], "start": ev['timestamp']}
        elif ev['event'] == "on_boot":
            if current_run: runs.append(current_run)
            current_run = {"type": "System", "events": [ev], "start": ev['timestamp']}
        elif current_run:
            current_run['events'].append(ev)
            
    if current_run: runs.append(current_run)

    # Show last N runs
    target_runs = runs[-last:]
    
    console.print(f"[bold purple]KOR Execution Trace (Last {len(target_runs)} runs)[/bold purple]\n")
    
    for i, run in enumerate(target_runs):
        dt = datetime.fromtimestamp(run['start']).strftime('%Y-%m-%d %H:%M:%S')
        run_tree = Tree(f"[bold cyan]Run {i+1}[/bold cyan] ({run['type']}) - {dt}")
        
        for ev in run['events']:
            ev_name = ev['event']
            data = ev.get('data', {})
            
            if ev_name == "on_agent_start":
                run_tree.add(f"[green]▶ Agent Started[/green]: {data.get('input', '...')}")
            elif ev_name == "on_node_start":
                run_tree.add(f"[yellow]⚙ Entering Node[/yellow]: [bold]{data.get('node', 'unknown')}[/bold]")
            elif ev_name == "on_agent_end":
                run_tree.add("[blue]⏹ Agent Finished[/blue]")
            elif ev_name == "on_boot":
                run_tree.add("[dim]⟳ System Boot[/dim]")
            else:
                if show_all:
                    run_tree.add(f"[dim]{ev_name}[/dim]")
                    
        console.print(run_tree)
        console.print("")
