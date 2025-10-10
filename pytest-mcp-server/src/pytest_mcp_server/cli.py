"""
Command-line interface for the pytest MCP server.
"""

import asyncio
import logging
import os
from pathlib import Path

import click
from rich.console import Console
from rich.logging import RichHandler

from .server import create_server


# Configure logging with Rich
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)

logger = logging.getLogger(__name__)


@click.group()
@click.version_option()
@click.option("--debug", is_flag=True, help="Enable debug logging")
def main(debug: bool) -> None:
    """Pytest MCP Server - AI-enhanced testing framework integration."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")


@main.command()
@click.option(
    "--db-path",
    type=click.Path(),
    help="Path to SQLite database file (default: in-memory)"
)
def serve(db_path: str) -> None:
    """Start the MCP server (STDIO mode)."""
    try:
        # Set database path if provided
        if db_path:
            os.environ["PYTEST_MCP_DB_PATH"] = str(Path(db_path).resolve())

        # Create and run the server
        app = create_server()

        console.print(f"🚀 Starting Pytest MCP Server (STDIO)", style="bold green")
        if db_path:
            console.print(f"   Database: {db_path}")
        console.print(f"   Protocol: MCP over STDIO", style="dim")
        console.print(f"   Use Ctrl+C to stop", style="dim")

        # Run the FastMCP server (uses STDIO by default)
        app.run()

    except KeyboardInterrupt:
        console.print("\n👋 Shutting down server...", style="bold yellow")
    except Exception as e:
        console.print(f"❌ Error starting server: {e}", style="bold red")
        raise click.ClickException(str(e))


@main.command()
@click.argument("tool_name")
@click.argument("args", required=False)
@click.option(
    "--server-url",
    default="http://localhost:8000",
    help="MCP server URL",
    show_default=True
)
def call(tool_name: str, args: str, server_url: str) -> None:
    """Call an MCP server tool directly."""
    import json
    import httpx

    try:
        # Parse arguments
        tool_args = {}
        if args:
            try:
                tool_args = json.loads(args)
            except json.JSONDecodeError as e:
                raise click.ClickException(f"Invalid JSON in args: {e}")

        console.print(f"📞 Calling tool: {tool_name}")
        if tool_args:
            console.print(f"   Args: {json.dumps(tool_args, indent=2)}")

        # Make HTTP request to server
        with httpx.Client() as client:
            response = client.post(
                f"{server_url}/tools/{tool_name}",
                json=tool_args,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

        console.print("✅ Response:", style="bold green")
        console.print_json(json.dumps(result, indent=2))

    except httpx.HTTPError as e:
        console.print(f"❌ HTTP Error: {e}", style="bold red")
        raise click.ClickException(str(e))
    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")
        raise click.ClickException(str(e))


@main.command()
@click.option(
    "--server-url",
    default="http://localhost:8000",
    help="MCP server URL",
    show_default=True
)
def tools(server_url: str) -> None:
    """List available MCP server tools."""
    import httpx

    try:
        console.print("🔍 Fetching available tools...")

        with httpx.Client() as client:
            response = client.get(f"{server_url}/tools", timeout=10.0)
            response.raise_for_status()
            tools_list = response.json()

        if not tools_list:
            console.print("No tools available", style="yellow")
            return

        console.print(f"\n📋 Available Tools ({len(tools_list)}):", style="bold blue")

        for tool in tools_list:
            console.print(f"\n  🔧 {tool['name']}", style="bold")
            console.print(f"     {tool.get('description', 'No description')}")

            if 'inputSchema' in tool and 'properties' in tool['inputSchema']:
                console.print("     Parameters:", style="dim")
                for param, details in tool['inputSchema']['properties'].items():
                    param_type = details.get('type', 'unknown')
                    required = param in tool['inputSchema'].get('required', [])
                    req_marker = " (required)" if required else " (optional)"
                    console.print(f"       • {param}: {param_type}{req_marker}", style="dim")

    except httpx.HTTPError as e:
        console.print(f"❌ HTTP Error: {e}", style="bold red")
        raise click.ClickException(str(e))
    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")
        raise click.ClickException(str(e))


@main.command()
@click.option(
    "--output",
    "-o",
    type=click.File("w"),
    default="-",
    help="Output file (default: stdout)"
)
def config(output) -> None:
    """Generate MCP client configuration."""
    config_data = {
        "mcpServers": {
            "pytest-mcp": {
                "command": "pytest-mcp-server",
                "args": ["serve"],
                "env": {
                    "PYTEST_MCP_DB_PATH": "./pytest_mcp.db"
                }
            }
        }
    }

    import json
    json.dump(config_data, output, indent=2)
    output.write("\n")

    if output != click.get_text_stream("stdout"):
        console.print(f"✅ Configuration written to {output.name}")


@main.command()
@click.argument("session_id", required=False)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "table", "summary"]),
    default="summary",
    help="Output format"
)
def status(session_id: str, output_format: str) -> None:
    """Show test session status."""
    # This would connect to the running server and get status
    console.print("💡 This command requires a running MCP server", style="yellow")
    console.print("   Use 'pytest-mcp-server serve' to start the server first")


@main.command()
@click.argument("pattern", required=False)
@click.option(
    "--limit",
    default=10,
    type=int,
    help="Maximum number of results"
)
def failures(pattern: str, limit: int) -> None:
    """Search for test failures by pattern."""
    console.print("💡 This command requires a running MCP server", style="yellow")
    console.print("   Use 'pytest-mcp-server serve' to start the server first")


if __name__ == "__main__":
    main()