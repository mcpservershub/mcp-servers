from llm_sandbox import SandboxBackend, SandboxSession
from mcp.server.fastmcp import FastMCP

mcp = FastMCP()

@mcp.tool()
def start_sandbox(
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
        with SandboxSession(
            backend=SandboxBackend.DOCKER,
            dockerfile=sandbox_source if "Dockerfile" in sandbox_source else None,
            image=sandbox_source if "Dockerfile" not in sandbox_source else None,
            lang=lang,
            keep_template=keep_template,
        ) as session:
            output = session.run(code)

            if output_file_path:
                with open(output_file_path, "w") as f:
                    f.write(output.text)

            return {"status": "Code executed successfully.", "output": output.text, "exit_code": output.exit_code}
    except Exception as e:
        return {"status": "Failed to start or execute in sandbox.", "error": str(e)}

@mcp.tool()
def list_sandboxes():
    """
    Lists active sandbox environments.
    """
    try:
        # Placeholder: In a real scenario, this would interact with the llm-sandbox backend
        # to list active sessions or templates.
        return {"status": "Not implemented yet. Placeholder for listing sandboxes."}
    except Exception as e:
        return {"status": "Failed to list sandboxes.", "error": str(e)}

@mcp.tool()
def stop_sandbox(session_id: str):
    """
    Stops and cleans up a specific sandbox session.

    :param session_id: The ID of the sandbox session to stop.
    """
    try:
        # Placeholder: In a real scenario, this would interact with the llm-sandbox backend
        # to stop and clean up a specific session.
        return {"status": f"Not implemented yet. Placeholder for stopping sandbox session {session_id}."}
    except Exception as e:
        return {"status": "Failed to stop sandbox.", "error": str(e)}

@mcp.tool()
def list_sandboxes():
    """
    Lists active sandbox environments.
    """
    try:
        # Placeholder: In a real scenario, this would interact with the llm-sandbox backend
        # to list active sessions or templates.
        return {"status": "Not implemented yet. Placeholder for listing sandboxes."}
    except Exception as e:
        return {"status": "Failed to list sandboxes.", "error": str(e)}

@mcp.tool()
def stop_sandbox(session_id: str):
    """
    Stops and cleans up a specific sandbox session.

    :param session_id: The ID of the sandbox session to stop.
    """
    try:
        # Placeholder: In a real scenario, this would interact with the llm-sandbox backend
        # to stop and clean up a specific session.
        return {"status": f"Not implemented yet. Placeholder for stopping sandbox session {session_id}."}
    except Exception as e:
        return {"status": "Failed to stop sandbox.", "error": str(e)}

if __name__ == "__main__":
    mcp.run()
