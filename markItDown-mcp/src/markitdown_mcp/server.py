from os import listdir
from typing import Tuple

import mcp.types as types
from markitdown import MarkItDown
from mcp.server import NotificationOptions, Server, models, stdio

PROMPTS = {
    "md": types.Prompt(
        name="md",
        description="Convert document to markdown format using MarkItDown",
        arguments=[
            types.PromptArgument(
                name="file_path",
                description="A URI to any document or file",
                required=True,
            )
        ],
    ),
    "ls": types.Prompt(
        name="ls",
        description="list files in a directory",
        arguments=[
            types.PromptArgument(
                name="directory",
                description="directory to list files",
                required=True,
            )
        ],
    ),
}


def convert_to_markdown(file_path: str) -> Tuple[str | None, str]:
    try:
        md = MarkItDown()
        result = md.convert(file_path)
        return result.title, result.text_content

    except Exception as e:
        return None, f"Error converting document: {str(e)}"


# Initialize server
app = Server("document-conversion-server")


@app.list_prompts()
async def list_prompts() -> list[types.Prompt]:
    return list(PROMPTS.values())


@app.get_prompt()
async def get_prompt(
    name: str, arguments: dict[str, str] | None = None
) -> types.GetPromptResult:
    if name not in PROMPTS:
        raise ValueError(f"Prompt not found: {name}")

    if name == "md":
        if not arguments:
            raise ValueError("Arguments required")

        file_path = arguments.get("file_path")

        if not file_path:
            raise ValueError("file_path is required")

        try:
            markdown_title, markdown_content = convert_to_markdown(file_path)

            return types.GetPromptResult(
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=f"Here is the converted document in markdown format:\n{'' if not markdown_title else markdown_title}\n{markdown_content}",
                        ),
                    )
                ]
            )

        except Exception as e:
            raise ValueError(f"Error processing document: {str(e)}")

    elif name == "ls":
        try:
            directory = arguments["directory"]
            files = listdir(directory)

            # Format the output in a structured, informative way
            file_count = len(files)
            formatted_output = f"Directory listing for: {directory}\n"
            formatted_output += f"Total files: {file_count}\n\n"

            # Group files by type if possible
            extensions = {}
            no_extension = []

            for file in files:
                if "." in file:
                    ext = file.split(".")[-1].lower()
                    if ext not in extensions:
                        extensions[ext] = []
                    extensions[ext].append(file)
                else:
                    no_extension.append(file)

            # Add file groupings to output
            if extensions:
                formatted_output += "Files by type:\n"
                for ext, files_of_type in extensions.items():
                    formatted_output += f"- {ext.upper()} files ({len(files_of_type)}): {', '.join(files_of_type)}\n"

            if no_extension:
                formatted_output += f"\nFiles without extension ({len(no_extension)}): {', '.join(no_extension)}\n"

            # Add complete listing
            formatted_output += "\nComplete file listing:\n"
            for idx, file in enumerate(sorted(files), 1):
                formatted_output += f"{idx}. {file}\n"

            return types.GetPromptResult(
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=formatted_output,
                        ),
                    )
                ]
            )
        except Exception as e:
            raise ValueError(f"Error listing directory: {str(e)}")
    raise ValueError("Prompt implementation not found")


async def run():
    async with stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            models.InitializationOptions(
                server_name="example",
                server_version="0.1.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
