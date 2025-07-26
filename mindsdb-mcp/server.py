from typing import Dict, List
from mcp.server.fastmcp import FastMCP
from minds.client import Client

# Import configuration
from config import (
    MINDS_BASE_URL,
    FASTMCP_DEBUG,
    FASTMCP_LOG_LEVEL,
    FASTMCP_HOST,
    FASTMCP_PORT,
    FASTMCP_SSE_PATH,
    FASTMCP_MESSAGE_PATH,
)

# Create the MCP server with customized settings
mcp = FastMCP(
    "Minds Enterprise",
    debug=FASTMCP_DEBUG,
    log_level=FASTMCP_LOG_LEVEL,
    host=FASTMCP_HOST,
    port=FASTMCP_PORT,
    sse_path=FASTMCP_SSE_PATH,
    message_path=FASTMCP_MESSAGE_PATH,
)


@mcp.resource("minds://{api_key}", mime_type="application/json")
def get_minds(api_key: str) -> List[Dict]:
    """
    Returns a list of available Minds for completion.

    Args:
        api_key: The Minds API key

    Returns:
        A list of Mind objects
    """
    minds_client = Client(api_key, base_url=MINDS_BASE_URL)
    all_minds = minds_client.minds.list()
    all_mind_objs = []
    for mind in all_minds:
        all_mind_objs.append(
            {
                "name": mind.name,
                "model_name": mind.model_name,
                "provider": mind.provider,
                "parameters": mind.parameters,
                "datasources": mind.datasources,
                "created_at": mind.created_at,
                "updated_at": mind.updated_at,
            }
        )
    return all_mind_objs


@mcp.resource("minds://{mind_name}/{api_key}", mime_type="application/json")
def get_mind(mind_name: str, api_key: str) -> Dict:
    """
    Gets a Mind by name.

    Args:
        mind_name: The name of the Mind to retrieve
        api_key: The Minds API key

    Returns:
        A Mind object
    """
    minds_client = Client(api_key, base_url=MINDS_BASE_URL)
    mind = minds_client.minds.get(mind_name)
    return {
        "name": mind.name,
        "model_name": mind.model_name,
        "provider": mind.provider,
        "parameters": mind.parameters,
        "datasources": mind.datasources,
        "created_at": mind.created_at,
        "updated_at": mind.updated_at,
    }


@mcp.tool()
def completion(mind_name: str, message: str, api_key: str) -> str:
    """
    Generate a completion using the specified Mind.

    Args:
        mind_name: The ID of the Mind to use for completion
        message: The message to complete
        api_key: The Minds API key

    Returns:
        A completion response, either as a string or as a stream of chunks
    """
    minds_client = Client(api_key, base_url=MINDS_BASE_URL)
    mind = minds_client.minds.get(mind_name)
    return mind.completion(message)


if __name__ == "__main__":
    # Run the server - FastMCP already has host and port from initialization
    mcp.run()
