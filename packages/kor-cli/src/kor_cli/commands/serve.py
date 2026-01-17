import click
from rich.console import Console

console = Console()

@click.command()
def serve():
    """Starts the KOR MCP Server."""
    console.print("[bold blue]Starting KOR MCP Server...[/]")
    console.print("KOR is now available as an MCP server via stdio.")
    console.print("Tools: terminal, browser, read_file, write_file, list_dir")
    console.print("\n[dim]Press Ctrl+C to stop.[/dim]\n")
    
    try:
        from kor_core.server import run_server
        run_server()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Server stopped.[/]")
