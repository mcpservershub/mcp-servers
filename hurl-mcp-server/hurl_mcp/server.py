"""Hurl MCP Server implementation."""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("hurl-mcp-server")


def run_hurl_command(
    args: List[str], 
    input_text: Optional[str] = None,
    cwd: Optional[str] = None
) -> Dict[str, Any]:
    """Execute hurl command and return results."""
    try:
        # Ensure hurl is in the command
        if args[0] != "hurl":
            args = ["hurl"] + args
        
        # Run the command
        result = subprocess.run(
            args,
            input=input_text,
            text=True,
            capture_output=True,
            cwd=cwd
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except FileNotFoundError:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Hurl CLI not found. Please ensure hurl is installed and in PATH.",
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Error executing hurl: {str(e)}",
            "returncode": -1
        }


@mcp.tool()
def run_hurl(
    hurl_file: str,
    output_format: Optional[str] = None,
    output_file: Optional[str] = None,
    verbose: bool = False,
    insecure: bool = False,
    location: bool = False,
    max_time: Optional[int] = None
) -> Dict[str, Any]:
    """
    Execute a .hurl file and return the response.
    
    Args:
        hurl_file: Path to the .hurl file
        output_format: Output format (json, or None for default)
        output_file: Path to save the output
        verbose: Enable verbose output
        insecure: Allow insecure SSL connections
        location: Follow redirects
        max_time: Maximum time in seconds for the request
    
    Returns:
        Dictionary containing execution results
    """
    args = []
    
    if output_format == "json":
        args.append("--json")
    
    if output_file:
        args.extend(["--output", output_file])
    
    if verbose:
        args.append("--verbose")
    
    if insecure:
        args.append("--insecure")
    
    if location:
        args.append("--location")
    
    if max_time:
        args.extend(["--max-time", str(max_time)])
    
    args.append(hurl_file)
    
    result = run_hurl_command(args)
    
    # Parse JSON output if requested
    if output_format == "json" and result["success"] and result["stdout"]:
        try:
            result["parsed_output"] = json.loads(result["stdout"])
        except json.JSONDecodeError:
            result["parsed_output"] = None
    
    # Add output file info to result
    if output_file and result["success"]:
        result["output_file"] = output_file
        result["message"] = f"Output saved to {output_file}"
    
    return result


@mcp.tool()
def run_hurl_test(
    hurl_file: str,
    report_format: Optional[str] = None,
    report_path: Optional[str] = None,
    output_file: Optional[str] = None,
    continue_on_error: bool = False,
    retry: Optional[int] = None,
    parallel: bool = False,
    jobs: Optional[int] = None
) -> Dict[str, Any]:
    """
    Execute a .hurl file in test mode.
    
    Args:
        hurl_file: Path to the .hurl file or directory
        report_format: Report format (html, json, junit, tap)
        report_path: Path where to save the report
        output_file: Path to save the test output
        continue_on_error: Continue on assertion errors
        retry: Number of retries for failed requests
        parallel: Run tests in parallel
        jobs: Number of parallel jobs
    
    Returns:
        Dictionary containing test results
    """
    args = ["--test"]
    
    if output_file:
        args.extend(["--output", output_file])
    
    if report_format and report_path:
        if report_format == "html":
            args.extend(["--report-html", report_path])
        elif report_format == "json":
            args.extend(["--report-json", report_path])
        elif report_format == "junit":
            args.extend(["--report-junit", report_path])
        elif report_format == "tap":
            args.extend(["--report-tap", report_path])
    
    if continue_on_error:
        args.append("--continue-on-error")
    
    if retry is not None:
        args.extend(["--retry", str(retry)])
    
    if parallel:
        args.append("--parallel")
        
    if jobs is not None:
        args.extend(["--jobs", str(jobs)])
    
    args.append(hurl_file)
    
    result = run_hurl_command(args)
    
    # Add output file info to result
    if output_file and result["success"]:
        result["output_file"] = output_file
        result["message"] = f"Test output saved to {output_file}"
    
    return result


@mcp.tool()
def run_hurl_with_variables(
    hurl_file: str,
    variables: Dict[str, str],
    variables_file: Optional[str] = None,
    output_format: Optional[str] = None,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute a .hurl file with custom variables.
    
    Args:
        hurl_file: Path to the .hurl file
        variables: Dictionary of variables to pass
        variables_file: Path to variables file (alternative to variables dict)
        output_format: Output format (json, or None for default)
        output_file: Path to save the output
    
    Returns:
        Dictionary containing execution results
    """
    args = []
    
    # Add variables from dictionary
    for name, value in variables.items():
        args.extend(["--variable", f"{name}={value}"])
    
    # Add variables file if provided
    if variables_file:
        args.extend(["--variables-file", variables_file])
    
    if output_format == "json":
        args.append("--json")
    
    if output_file:
        args.extend(["--output", output_file])
    
    args.append(hurl_file)
    
    result = run_hurl_command(args)
    
    # Add output file info to result
    if output_file and result["success"]:
        result["output_file"] = output_file
        result["message"] = f"Output saved to {output_file}"
    
    return result


@mcp.tool()
def run_hurl_parallel(
    hurl_files: List[str],
    jobs: Optional[int] = None,
    test_mode: bool = True,
    continue_on_error: bool = False,
    output_file: Optional[str] = None,
    report_format: Optional[str] = None,
    report_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute multiple .hurl files in parallel.
    
    Args:
        hurl_files: List of paths to .hurl files
        jobs: Number of parallel jobs (defaults to CPU count)
        test_mode: Run in test mode
        continue_on_error: Continue on errors
        output_file: Path to save the output
        report_format: Report format (html, json, junit, tap) - only for test mode
        report_path: Path where to save the report - only for test mode
    
    Returns:
        Dictionary containing execution results
    """
    args = ["--parallel"]
    
    if test_mode:
        args.append("--test")
    
    if jobs is not None:
        args.extend(["--jobs", str(jobs)])
    
    if continue_on_error:
        args.append("--continue-on-error")
    
    if output_file:
        args.extend(["--output", output_file])
    
    # Add report options if in test mode
    if test_mode and report_format and report_path:
        if report_format == "html":
            args.extend(["--report-html", report_path])
        elif report_format == "json":
            args.extend(["--report-json", report_path])
        elif report_format == "junit":
            args.extend(["--report-junit", report_path])
        elif report_format == "tap":
            args.extend(["--report-tap", report_path])
    
    args.extend(hurl_files)
    
    result = run_hurl_command(args)
    
    # Add output file info to result
    if output_file and result["success"]:
        result["output_file"] = output_file
        result["message"] = f"Output saved to {output_file}"
    
    return result


@mcp.tool()
def validate_hurl(
    hurl_content: str,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate .hurl file syntax without executing requests.
    
    Args:
        hurl_content: Content of the .hurl file to validate
        output_file: Path to save the validation results
    
    Returns:
        Dictionary containing validation results
    """
    # Create a temporary file with the content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.hurl', delete=False) as f:
        f.write(hurl_content)
        temp_file = f.name
    
    try:
        # Use --no-output to avoid actually running requests
        # Just parse the file
        args = ["--no-output", temp_file]
        result = run_hurl_command(args)
        
        # Check if there were parsing errors
        if "error:" in result["stderr"].lower():
            result["valid"] = False
            result["errors"] = result["stderr"]
        else:
            result["valid"] = True
            result["errors"] = None
        
        # Save validation results to file if requested
        if output_file:
            validation_report = {
                "valid": result["valid"],
                "errors": result["errors"],
                "stderr": result["stderr"],
                "stdout": result["stdout"],
                "returncode": result["returncode"]
            }
            try:
                Path(output_file).parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, 'w') as f:
                    json.dump(validation_report, f, indent=2)
                result["output_file"] = output_file
                result["message"] = f"Validation results saved to {output_file}"
            except Exception as e:
                result["save_error"] = f"Failed to save validation results: {str(e)}"
        
        return result
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file)
        except:
            pass


@mcp.tool()
def create_hurl_file(
    file_path: str,
    content: str
) -> Dict[str, Any]:
    """
    Create a .hurl file with the specified content.
    
    Args:
        file_path: Path where to create the .hurl file
        content: Content of the .hurl file
    
    Returns:
        Dictionary containing operation result
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        
        return {
            "success": True,
            "message": f"Created .hurl file at {file_path}",
            "file_path": str(path.absolute())
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to create .hurl file: {str(e)}",
            "file_path": None
        }


def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()