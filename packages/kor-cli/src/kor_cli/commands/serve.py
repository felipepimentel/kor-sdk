import click
from rich.console import Console

console = Console()

@click.command()
@click.option("--mode", type=click.Choice(["mcp", "openai"]), default="mcp", help="Server mode (mcp or openai)")
@click.option("--host", default="0.0.0.0", help="Host to bind (for openai mode)")
@click.option("--port", default=8000, help="Port to bind (for openai mode)")
def serve(mode, host, port):
    """Starts the KOR Server (MCP or OpenAI API)."""
    if mode == "mcp":
        console.print("[bold blue]Starting KOR MCP Server...[/]")
        console.print("KOR is now available as an MCP server via stdio.")
        console.print("Tools: terminal, browser, read_file, write_file, list_dir")
        console.print("\n[dim]Press Ctrl+C to stop.[/dim]\n")
        
        try:
            from kor_core.server import run_server
            run_server()
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Server stopped.[/]")
    else:
        console.print(f"[bold blue]Starting KOR OpenAI-Compatible API Server on {host}:{port}...[/]")
        try:
            # We try to import from the plugin. If it's not installed, we inform the user.
            try:
                from kor_plugin_openai_api.main import run
                run(host=host, port=port)
            except ImportError:
                console.print("[bold red]Error:[/bold red] kor-plugin-openai-api is not installed.")
                console.print("Install it with: [bold blue]uv sync[/bold blue] or [bold blue]pip install plugins/kor-plugin-openai-api[/bold blue]")
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Server stopped.[/]")
