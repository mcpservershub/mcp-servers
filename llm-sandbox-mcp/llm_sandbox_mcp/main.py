import os

from llm_sandbox import SandboxBackend, SandboxSession
from mcp.server.fastmcp import FastMCP

mcp = FastMCP()

@mcp.tool()
def execute_code(
    sandbox_source: str,
    code: str,
    keep_template: bool = False,
    lang: str = "python",
    output_file_path: str = None
):
    """
    Starts a sandbox environment and executes code.

    :param sandbox_source: The source for the sandbox, which can be a Dockerfile path or an image name.
    :param code: The code to execute in the sandbox.
    :param keep_template: If True, the sandbox resources (container and data) will be persisted.
    :param lang: The programming language for the sandbox.
    :param output_file_path: Optional path to a file where the sandbox output will be written.
    """
    try:
        # Check if the code parameter is a file path
        if os.path.exists(code):
            with open(code, "r") as f:
                code_to_execute = f.read()
        else:
            code_to_execute = code

        with SandboxSession(
            backend=SandboxBackend.DOCKER,
            dockerfile=sandbox_source if "Dockerfile" in sandbox_source else None,
            image=sandbox_source if "Dockerfile" not in sandbox_source else None,
            lang=lang,
            keep_template=True,  # Explicitly keep the container running
            commit_container=False,  # Do not remove the container after execution
        ) as session:
            output = session.run(code_to_execute)

            if output_file_path:
                with open(output_file_path, "w") as f:
                    f.write(output.text)

            return {"status": "Code executed successfully.", "output": output.text, "exit_code": output.exit_code}
    except Exception as e:
        return {"status": "Failed to start or execute in sandbox.", "error": str(e)}


if __name__ == "__main__":
    mcp.run()
