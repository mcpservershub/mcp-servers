"""
OneFileLLM MCP Server Package

A lightweight MCP server for OneFileLLM with essential features.
"""

__version__ = "1.0.0"
__author__ = "OneFileLLM MCP Contributors"

from .server import (
    create_server,
    run_server,
    mcp,
    # Exported tools
    github_repo,
    github_issue,
    github_pr,
    crawl_web,
    youtube_transcript,
    arxiv_paper,
    count_tokens,
)

__all__ = [
    "create_server",
    "run_server",
    "mcp",
    "github_repo",
    "github_issue",
    "github_pr",
    "crawl_web",
    "youtube_transcript",
    "arxiv_paper",
    "count_tokens",
]