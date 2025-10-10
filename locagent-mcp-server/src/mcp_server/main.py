"""
Command-line interface for LocAgent MCP Server using FastMCP
"""

import click
import logging
from .server import app


@click.command()
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default="INFO",
    help="Set the logging level"
)
@click.option(
    "--log-file",
    type=click.Path(),
    help="Log file path (optional)"
)
def main(log_level: str, log_file: str) -> None:
    """Start the LocAgent MCP Server using FastMCP.
    
    This server exposes LocAgent's code localization tools through the Model Context Protocol,
    allowing LLM clients to search and analyze codebases.
    
    Usage:
        locagent-mcp-server
        locagent-mcp-server --log-level DEBUG
        locagent-mcp-server --log-file /tmp/mcp-server.log
    """
    # Configure logging
    log_config = {
        "level": getattr(logging, log_level),
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    }
    
    if log_file:
        log_config["filename"] = log_file
    
    logging.basicConfig(**log_config)
    
    # Start the FastMCP server
    try:
        click.echo("Starting LocAgent MCP Server with FastMCP...", err=True)
        app.run(transport="stdio")
    except KeyboardInterrupt:
        click.echo("Server stopped by user.", err=True)
    except Exception as e:
        click.echo(f"Server error: {e}", err=True)
        raise


if __name__ == "__main__":
    main()