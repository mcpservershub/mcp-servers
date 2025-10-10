"""
FastMCP server exposing a single async tool: ingest_gitrepo.
Uses gitingest.ingest_async to fetch repo or local directory content,
and writes that content to a file.
"""

from typing import Annotated
import os
# import asyncio
import logging
# from typing import Optional

from gitingest import ingest_async
from mcp.server.fastmcp import FastMCP
from pydantic import Field

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s ▶ %(message)s",
)
logger = logging.getLogger(__name__)

mcp = FastMCP("GitIngestServer")


@mcp.tool()
async def ingest_gitrepo(
        input:Annotated[
            str,
            Field(
        description="The source input path to ingest, which can be either an URL or Local directory"
    ),
    ],
        output_file: Annotated[
        str,
        Field(
            description="The output path to which the ingested content will be written transport"
        ),
    ]
)-> str:
    """
    Ingests a local directory or GitHub repository and writes the content to an output file.

    Args:
        input (str): Local directory path or GitHub repository URL.
        output_file (str): Path to the file where content will be written.
        
    Raises:
        FileNotFoundError: If the input path does not exist and is not a valid URL.
        RuntimeError: If the ingestion fails.
        ValueError: If no content is returned.
        IOError: If writing to the output file fails.
    """

    _, _, content = await ingest_async(input)

    # Check for empty content
    if not content:
        raise ValueError(f"No content found in path '{input}'")

    # File writing with error handling
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(str(content))
    except IOError as e:
        raise IOError(f"Failed to write files: {str(e)}")

    logger.info("Successfully wrtten ingested content to %s", output_file)
    return content


def main():
    """
    Starts the FastMCP server on the STDIO.
    """
    logger.info("Starting FastMCP server…")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
