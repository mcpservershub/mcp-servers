import os
import logging

from llm_sandbox import SandboxBackend, SandboxSession
from mcp.server.fastmcp import FastMCP
from mcp.types import ImageContent, TextContent

logger = logging.getLogger(__name__)

mcp = FastMCP()

def _supports_visualization(language: str) -> bool:
    return language.lower() in ["python", "r"]

@mcp.tool()
def execute_code(
    code: str,
    sandbox_source: str = None,
    language: str = "python",
    libraries: list[str] | None = None,
    timeout: int = 30,
    keep_template: bool = True,
    output_file_path: str = None
) -> list[ImageContent | TextContent]:
    """
    Starts a sandbox environment and executes code.

    :param code: The code to execute in the sandbox (or file path to code).
    :param sandbox_source: The source for the sandbox, which can be a Dockerfile path or an image name.
    :param language: The programming language for the sandbox.
    :param libraries: List of libraries to install before execution.
    :param timeout: Execution timeout in seconds.
    :param keep_template: If True, the sandbox resources (container and data) will be persisted.
    :param output_file_path: Optional path to a file where the sandbox output will be written.
    """
    results: list[ImageContent | TextContent] = []
    
    try:
        # Check if the code parameter is a file path (keep existing file handling)
        if os.path.exists(code):
            with open(code, "r") as f:
                code_to_execute = f.read()
        else:
            code_to_execute = code

        # Use regular SandboxSession (ArtifactSandboxSession not available in current version)
        session_cls = SandboxSession
        
        session_kwargs = {
            "lang": language,
            "keep_template": keep_template,
            "verbose": False,
            "backend": SandboxBackend.DOCKER,  # Keep hardcoded Docker backend
            "session_timeout": timeout,
        }
        
        # Add sandbox source parameters if provided
        if sandbox_source:
            if "Dockerfile" in sandbox_source:
                session_kwargs["dockerfile"] = sandbox_source
            else:
                session_kwargs["image"] = sandbox_source

        with session_cls(**session_kwargs) as session:
            result = session.run(
                code=code_to_execute,
                libraries=libraries or [],
            )

            # Add text result (simplified for current llm-sandbox version)
            if hasattr(result, 'to_json'):
                results.append(TextContent(text=result.to_json(), type="text"))
            elif hasattr(result, 'text'):
                results.append(TextContent(text=result.text, type="text"))
            else:
                results.append(TextContent(text=str(result), type="text"))
            
            # Keep existing file output functionality
            if output_file_path:
                with open(output_file_path, "w") as f:
                    f.write(result.text if hasattr(result, 'text') else result.to_json())

    except Exception as e:
        logger.exception("Error executing code")
        error_result = {"exit_code": 1, "stderr": str(e), "stdout": "", "status": "error"}
        return [TextContent(text=str(error_result), type="text")]
    
    return results


if __name__ == "__main__":
    mcp.run()
