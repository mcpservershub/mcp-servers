"""
OneFileLLM MCP Server Core Implementation
"""

import os
import sys
import asyncio
import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_github_token() -> Optional[str]:
    """Setup GitHub token from environment"""
    token = os.getenv("GITHUB_TOKEN", "")
    if token:
        os.environ["GITHUB_TOKEN"] = token
        logger.info(f"GitHub token configured (length: {len(token)})")
        return token
    logger.warning("GitHub token not found in environment")
    return None


# Set GitHub token BEFORE importing onefilellm
GITHUB_TOKEN = setup_github_token()

# Import OneFileLLM
try:
    import onefilellm
    
    # Force set the token to ensure it's properly configured
    if GITHUB_TOKEN:
        onefilellm.TOKEN = GITHUB_TOKEN
        onefilellm.headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        
except ImportError as e:
    logger.error(f"Failed to import onefilellm: {e}")
    logger.error("Please install: pip install git+https://github.com/jimmc414/onefilellm.git")
    sys.exit(1)


# Initialize MCP server
mcp = FastMCP("OneFileLLM Simple")


# ===== GitHub Tools =====

@mcp.tool()
async def github_repo(url: str) -> str:
    """
    Fetch GitHub repository contents.
    
    Args:
        url: GitHub repository URL (e.g., https://github.com/user/repo)
    
    Returns:
        XML-formatted repository content
    """
    logger.info(f"Fetching GitHub repo: {url}")
    return await asyncio.to_thread(onefilellm.process_github_repo, url)


@mcp.tool()
async def github_issue(url: str) -> str:
    """
    Fetch GitHub issue with comments.
    
    Args:
        url: GitHub issue URL (e.g., https://github.com/user/repo/issues/123)
    
    Returns:
        XML-formatted issue content with comments
    """
    logger.info(f"Fetching GitHub issue: {url}")
    return await asyncio.to_thread(onefilellm.process_github_issue, url)


@mcp.tool()
async def github_pr(url: str) -> str:
    """
    Fetch GitHub pull request with diff.
    
    Args:
        url: GitHub PR URL (e.g., https://github.com/user/repo/pull/123)
    
    Returns:
        XML-formatted PR content with diff
    """
    logger.info(f"Fetching GitHub PR: {url}")
    return await asyncio.to_thread(onefilellm.process_github_pull_request, url)


# ===== Web Tools =====

@mcp.tool()
async def crawl_web(url: str, max_depth: int = 1) -> str:
    """
    Crawl website and extract text content.
    
    Args:
        url: Website URL to crawl
        max_depth: Maximum crawl depth (default: 1)
    
    Returns:
        XML-formatted extracted text content
    """
    logger.info(f"Crawling website: {url} (depth: {max_depth})")
    return await asyncio.to_thread(
        onefilellm.crawl_and_extract_text, 
        url, 
        max_depth, 
        False,  # include_pdfs
        True    # ignore_epubs
    )


@mcp.tool()
async def youtube_transcript(url: str) -> str:
    """
    Get YouTube video transcript.
    
    Args:
        url: YouTube video URL
    
    Returns:
        XML-formatted transcript
    """
    logger.info(f"Fetching YouTube transcript: {url}")
    return await asyncio.to_thread(onefilellm.fetch_youtube_transcript, url)


@mcp.tool()
async def arxiv_paper(url: str) -> str:
    """
    Fetch ArXiv paper content.
    
    Args:
        url: ArXiv paper URL
    
    Returns:
        XML-formatted paper content
    """
    logger.info(f"Fetching ArXiv paper: {url}")
    return await asyncio.to_thread(onefilellm.process_arxiv_pdf, url)


# ===== Utility Tools =====

@mcp.tool()
async def count_tokens(text: str) -> int:
    """
    Count tokens in text using tiktoken.
    
    Args:
        text: Text to count tokens for
    
    Returns:
        Number of tokens
    """
    count = await asyncio.to_thread(onefilellm.get_token_count, text)
    logger.info(f"Counted {count} tokens")
    return count


def create_server() -> FastMCP:
    """Factory function to create the MCP server"""
    return mcp


def run_server():
    """Run the MCP server with stdio transport"""
    logger.info("Starting OneFileLLM MCP Server...")
    logger.info(f"GitHub token status: {'configured' if GITHUB_TOKEN else 'not configured'}")
    # List available tools (FastMCP doesn't expose them directly)
    logger.info("Available tools: github_repo, github_issue, github_pr, crawl_web, youtube_transcript, arxiv_paper, count_tokens")
    
    mcp.run(transport="stdio")