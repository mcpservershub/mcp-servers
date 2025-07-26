import os

# Environment variables with defaults for Minds
MINDS_BASE_URL = os.environ.get("MINDS_BASE_URL", "https://mdb.ai")

# FastMCP settings
FASTMCP_DEBUG = os.environ.get("FASTMCP_DEBUG", "false").lower() == "true"
FASTMCP_LOG_LEVEL = os.environ.get("FASTMCP_LOG_LEVEL", "INFO")
FASTMCP_HOST = os.environ.get("FASTMCP_HOST", "0.0.0.0")
FASTMCP_PORT = int(os.environ.get("FASTMCP_PORT", "8000"))
FASTMCP_SSE_PATH = os.environ.get("FASTMCP_SSE_PATH", "/sse")
FASTMCP_MESSAGE_PATH = os.environ.get("FASTMCP_MESSAGE_PATH", "/messages/")
