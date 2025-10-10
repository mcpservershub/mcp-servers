"""
GnuCOBOL MCP Server Implementation

This module implements the FastMCP server with tools for GnuCOBOL compilation,
syntax checking, code analysis, and batch processing.
"""

import asyncio
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP application
app = FastMCP("gnucobol-mcp-server")


class COBOLCompilerError(Exception):
    """Custom exception for COBOL compiler errors"""
    pass


def check_cobc_available() -> bool:
    """
    Check if the cobc compiler is available in the system PATH.

    Returns:
        bool: True if cobc is available, False otherwise
    """
    return shutil.which("cobc") is not None


async def run_cobc_command(
    args: List[str],
    input_data: Optional[str] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Execute a cobc compiler command asynchronously.

    Args:
        args: List of command-line arguments for cobc
        input_data: Optional input to send to stdin
        timeout: Command timeout in seconds

    Returns:
        Dict containing stdout, stderr, and return_code

    Raises:
        COBOLCompilerError: If the command fails or times out
    """
    if not check_cobc_available():
        raise COBOLCompilerError(
            "GnuCOBOL compiler (cobc) not found. Please install GnuCOBOL: "
            "https://gnucobol.sourceforge.io/"
        )

    cmd = ["cobc"] + args

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE if input_data else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Communicate with timeout
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(
                    input=input_data.encode() if input_data else None
                ),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise COBOLCompilerError(f"Command timed out after {timeout} seconds")

        return {
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "return_code": process.returncode,
            "command": " ".join(cmd)
        }

    except FileNotFoundError:
        raise COBOLCompilerError("cobc command not found in PATH")
    except Exception as e:
        raise COBOLCompilerError(f"Failed to execute cobc: {str(e)}")


def validate_cobol_code(code: str) -> None:
    """
    Validate that the provided COBOL code is non-empty.

    Args:
        code: COBOL source code

    Raises:
        ValueError: If code is empty or invalid
    """
    if not code or not code.strip():
        raise ValueError("COBOL code cannot be empty")

    if len(code) > 1_000_000:  # 1MB limit
        raise ValueError("COBOL code exceeds maximum size of 1MB")


async def _compile_cobol_code(
    code: str,
    output_name: str = "program",
    options: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Internal helper to compile COBOL source code into an executable.
    Not exposed as a tool - used by compile_cobol and batch_compile.
    """
    try:
        # Validate input
        validate_cobol_code(code)

        # Create temporary directory for compilation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_file = temp_path / "source.cob"
            output_file = temp_path / output_name

            # Write source code to file
            source_file.write_text(code, encoding="utf-8")

            # Build compiler arguments
            compile_args = [
                "-x",  # Compile to executable
                "-o", str(output_file),  # Output path
                str(source_file)  # Source file
            ]

            # Add user-provided options
            if options:
                compile_args = options + compile_args

            # Run compilation
            result = await run_cobc_command(compile_args)

            success = result["return_code"] == 0

            response = {
                "success": success,
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "return_code": result["return_code"],
                "command": result["command"]
            }

            if success:
                response["message"] = f"Successfully compiled to executable: {output_name}"
                response["output_name"] = output_name
            else:
                response["message"] = "Compilation failed"
                response["error"] = result["stderr"]

            return response

    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Invalid input"
        }
    except COBOLCompilerError as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Compiler error"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Unexpected error during compilation"
        }


@app.tool()
async def compile_cobol(
    file_path: str,
    output_name: Optional[str] = None,
    options: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Compile a COBOL source file from filesystem into an executable.

    This tool reads a COBOL source file from the filesystem and compiles it
    into an executable binary using GnuCOBOL (cobc -x).

    Args:
        file_path: Path to the COBOL source file (absolute or relative)
        output_name: Name for the output executable (default: derived from file_path)
        options: Additional compiler options (e.g., ["-Wall", "-O2"])

    Returns:
        Dictionary containing:
            - success: Whether compilation succeeded
            - file_path: Path to source file that was compiled
            - output_name: Name of the compiled executable
            - stdout: Compiler standard output
            - stderr: Compiler standard error
            - return_code: Compiler exit code

    Example:
        >>> result = await compile_cobol(
        ...     file_path="/workspace/tests/sample_cobol/valid/calculator.cob",
        ...     output_name="calculator"
        ... )
    """
    try:
        # Validate and resolve file path
        source_path = Path(file_path)

        if not source_path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "message": "Source file does not exist"
            }

        if not source_path.is_file():
            return {
                "success": False,
                "error": f"Not a file: {file_path}",
                "message": "Path is not a regular file"
            }

        # Read the source code
        try:
            code = source_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return {
                "success": False,
                "error": "File encoding error - not valid UTF-8",
                "message": "Failed to read source file"
            }

        # Determine output name
        if output_name is None:
            output_name = source_path.stem  # filename without extension

        # Use the internal compile function
        result = await _compile_cobol_code(
            code=code,
            output_name=output_name,
            options=options
        )

        # Add file path to result
        result["file_path"] = str(source_path.absolute())

        return result

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error reading or compiling file"
        }


async def _syntax_check_code(
    code: str,
    options: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Internal helper to validate COBOL syntax without generating output.
    Not exposed as a tool - used by syntax_check and batch operations.
    """
    try:
        # Validate input
        validate_cobol_code(code)

        # Create temporary directory for syntax check
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_file = temp_path / "source.cob"

            # Write source code to file
            source_file.write_text(code, encoding="utf-8")

            # Build compiler arguments for syntax checking
            check_args = [
                "-fsyntax-only",  # Only check syntax
                str(source_file)  # Source file
            ]

            # Add user-provided options
            if options:
                check_args = options + check_args

            # Run syntax check
            result = await run_cobc_command(check_args)

            valid = result["return_code"] == 0
            stderr = result["stderr"]

            # Parse warnings and errors from stderr
            warnings = []
            errors = []
            for line in stderr.split("\n"):
                line = line.strip()
                if line:
                    if "warning:" in line.lower():
                        warnings.append(line)
                    elif "error:" in line.lower():
                        errors.append(line)

            response = {
                "valid": valid,
                "stdout": result["stdout"],
                "stderr": stderr,
                "return_code": result["return_code"],
                "command": result["command"],
                "warnings": warnings,
                "errors": errors,
                "warning_count": len(warnings),
                "error_count": len(errors)
            }

            if valid:
                response["message"] = "Syntax is valid"
                if warnings:
                    response["message"] += f" ({len(warnings)} warning(s))"
            else:
                response["message"] = f"Syntax check failed with {len(errors)} error(s)"

            return response

    except ValueError as e:
        return {
            "valid": False,
            "error": str(e),
            "message": "Invalid input"
        }
    except COBOLCompilerError as e:
        return {
            "valid": False,
            "error": str(e),
            "message": "Compiler error"
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "message": "Unexpected error during syntax check"
        }


@app.tool()
async def syntax_check(
    file_path: str,
    options: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Validate COBOL syntax from a source file without generating output.

    This tool reads a COBOL source file and performs syntax checking without
    creating any output files using GnuCOBOL (cobc -fsyntax-only).
    It's faster than full compilation and useful for quick validation.

    Args:
        file_path: Path to the COBOL source file (absolute or relative)
        options: Additional compiler options (e.g., ["-Wall", "-std=cobol2014"])

    Returns:
        Dictionary containing:
            - valid: Whether syntax is valid
            - file_path: Path to source file that was checked
            - stdout: Compiler standard output
            - stderr: Compiler messages and errors
            - return_code: Compiler exit code
            - warnings: List of warning messages
            - errors: List of error messages

    Example:
        >>> result = await syntax_check(
        ...     file_path="/workspace/tests/sample_cobol/valid/calculator.cob"
        ... )
    """
    try:
        # Validate and resolve file path
        source_path = Path(file_path)

        if not source_path.exists():
            return {
                "valid": False,
                "error": f"File not found: {file_path}",
                "message": "Source file does not exist"
            }

        if not source_path.is_file():
            return {
                "valid": False,
                "error": f"Not a file: {file_path}",
                "message": "Path is not a regular file"
            }

        # Read the source code
        try:
            code = source_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return {
                "valid": False,
                "error": "File encoding error - not valid UTF-8",
                "message": "Failed to read source file"
            }

        # Use the internal syntax_check function
        result = await _syntax_check_code(code=code, options=options)

        # Add file path to result
        result["file_path"] = str(source_path.absolute())

        return result

    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "message": "Error reading or checking file"
        }


async def _analyze_cobol_code(
    code: str,
    include_symbols: bool = True,
    include_xref: bool = True,
    options: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Internal helper to generate detailed code analysis and listings.
    Not exposed as a tool - used by analyze_cobol and batch operations.
    """
    try:
        # Validate input
        validate_cobol_code(code)

        # Create temporary directory for analysis
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_file = temp_path / "source.cob"

            # Write source code to file
            source_file.write_text(code, encoding="utf-8")

            # Create temporary listing file (required by -t flag)
            listing_file = temp_path / "listing.lst"

            # Build compiler arguments for analysis
            analyze_args = []

            # Add cross-reference if requested (uppercase -X)
            if include_xref:
                analyze_args.append("-X")

            # Add symbol table if requested
            if include_symbols:
                analyze_args.append("-ftsymbols")

            # Add listing generation flag with output file (-t requires a filename)
            analyze_args.extend(["-t", str(listing_file)])

            # Add syntax-only flag to prevent compilation/linking
            analyze_args.append("-fsyntax-only")

            # Add user-provided options
            if options:
                analyze_args.extend(options)

            # Add source file at the end
            analyze_args.append(str(source_file))

            # Run analysis
            result = await run_cobc_command(analyze_args)

            success = result["return_code"] == 0

            # Read listing from file if it exists
            if listing_file.exists():
                listing = listing_file.read_text(encoding="utf-8")
            else:
                listing = result["stdout"]

            # Parse basic analysis information
            analysis = {
                "lines_in_listing": len(listing.split("\n")),
                "has_symbols": include_symbols,
                "has_xref": include_xref
            }

            # Try to extract some basic info from stderr
            if "warning" in result["stderr"].lower():
                analysis["has_warnings"] = True
            if "error" in result["stderr"].lower():
                analysis["has_errors"] = True

            response = {
                "success": success,
                "listing": listing,
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "return_code": result["return_code"],
                "command": result["command"],
                "analysis": analysis
            }

            if success:
                response["message"] = "Analysis completed successfully"
            else:
                response["message"] = "Analysis completed with errors"
                response["error"] = result["stderr"]

            return response

    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Invalid input"
        }
    except COBOLCompilerError as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Compiler error"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Unexpected error during analysis"
        }


@app.tool()
async def analyze_cobol(
    file_path: str,
    include_symbols: bool = True,
    include_xref: bool = True,
    options: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate detailed code analysis and listings from a COBOL source file.

    This tool analyzes a COBOL source file and generates detailed listings including
    symbol tables and cross-reference information using GnuCOBOL (cobc -t -ftsymbols -Xref).
    Useful for understanding code structure and dependencies.

    Args:
        file_path: Path to the COBOL source file (absolute or relative)
        include_symbols: Include symbol table in output
        include_xref: Include cross-reference listing
        options: Additional compiler options

    Returns:
        Dictionary containing:
            - success: Whether analysis completed successfully
            - file_path: Path to source file that was analyzed
            - listing: Generated listing output
            - stdout: Compiler standard output
            - stderr: Compiler messages
            - return_code: Compiler exit code
            - analysis: Parsed analysis information

    Example:
        >>> result = await analyze_cobol(
        ...     file_path="/workspace/tests/sample_cobol/valid/calculator.cob",
        ...     include_symbols=True,
        ...     include_xref=True
        ... )
    """
    try:
        # Validate and resolve file path
        source_path = Path(file_path)

        if not source_path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "message": "Source file does not exist"
            }

        if not source_path.is_file():
            return {
                "success": False,
                "error": f"Not a file: {file_path}",
                "message": "Path is not a regular file"
            }

        # Read the source code
        try:
            code = source_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return {
                "success": False,
                "error": "File encoding error - not valid UTF-8",
                "message": "Failed to read source file"
            }

        # Use the internal analyze function
        result = await _analyze_cobol_code(
            code=code,
            include_symbols=include_symbols,
            include_xref=include_xref,
            options=options
        )

        # Add file path to result
        result["file_path"] = str(source_path.absolute())

        return result

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error reading or analyzing file"
        }


@app.tool()
async def batch_compile(
    file_paths: List[str],
    options: Optional[List[str]] = None,
    stop_on_error: bool = False
) -> Dict[str, Any]:
    """
    Compile multiple COBOL source files in batch.

    This tool compiles multiple COBOL source files from the filesystem, useful for
    processing several files at once. Each file is compiled independently.

    Args:
        file_paths: List of paths to COBOL source files (absolute or relative)
        options: Compiler options to apply to all programs
        stop_on_error: Stop batch if any compilation fails

    Returns:
        Dictionary containing:
            - total: Total number of programs
            - successful: Number of successful compilations
            - failed: Number of failed compilations
            - results: List of individual compilation results

    Example:
        >>> result = await batch_compile([
        ...     "/workspace/tests/sample_cobol/valid/hello.cob",
        ...     "/workspace/tests/sample_cobol/valid/calculator.cob"
        ... ])
    """
    try:
        # Validate input
        if not file_paths or not isinstance(file_paths, list):
            raise ValueError("file_paths must be a non-empty list")

        if len(file_paths) > 100:
            raise ValueError("Maximum 100 programs allowed per batch")

        results = []
        successful = 0
        failed = 0

        # Compile each program
        for i, file_path in enumerate(file_paths):
            try:
                # Validate file path
                source_path = Path(file_path)

                if not source_path.exists():
                    failed += 1
                    results.append({
                        "index": i,
                        "file_path": file_path,
                        "success": False,
                        "error": f"File not found: {file_path}",
                        "message": f"File not found: {file_path}"
                    })
                    if stop_on_error:
                        results.append({
                            "message": f"Stopping batch compilation after file not found at index {i}"
                        })
                        break
                    continue

                # Read the source code
                try:
                    code = source_path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    failed += 1
                    results.append({
                        "index": i,
                        "file_path": file_path,
                        "success": False,
                        "error": "File encoding error - not valid UTF-8",
                        "message": "Failed to read source file"
                    })
                    if stop_on_error:
                        results.append({
                            "message": f"Stopping batch compilation after encoding error at index {i}"
                        })
                        break
                    continue

                # Get output name from filename
                output_name = source_path.stem

                # Compile individual program
                compile_result = await _compile_cobol_code(
                    code=code,
                    output_name=output_name,
                    options=options
                )

                result_entry = {
                    "index": i,
                    "file_path": str(source_path.absolute()),
                    "output_name": output_name,
                    "success": compile_result["success"],
                    "return_code": compile_result.get("return_code", -1),
                    "stderr": compile_result.get("stderr", ""),
                    "stdout": compile_result.get("stdout", "")
                }

                if compile_result["success"]:
                    successful += 1
                    result_entry["message"] = f"Successfully compiled {output_name}"
                else:
                    failed += 1
                    result_entry["message"] = f"Failed to compile {output_name}"
                    result_entry["error"] = compile_result.get("error", "Unknown error")

                results.append(result_entry)

                # Stop on error if requested
                if stop_on_error and not compile_result["success"]:
                    results.append({
                        "message": f"Stopping batch compilation after failure at index {i} ({file_path})"
                    })
                    break

            except Exception as e:
                failed += 1
                results.append({
                    "index": i,
                    "file_path": file_path,
                    "success": False,
                    "error": str(e),
                    "message": f"Exception while compiling {file_path}"
                })

                if stop_on_error:
                    results.append({
                        "message": f"Stopping batch compilation after exception at index {i} ({file_path})"
                    })
                    break

        return {
            "total": len(file_paths),
            "successful": successful,
            "failed": failed,
            "success_rate": f"{(successful / len(file_paths) * 100):.1f}%" if file_paths else "0.0%",
            "results": results,
            "message": f"Batch compilation complete: {successful} successful, {failed} failed"
        }

    except ValueError as e:
        return {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "error": str(e),
            "message": "Invalid input for batch compilation"
        }
    except Exception as e:
        return {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "error": str(e),
            "message": "Unexpected error during batch compilation"
        }


@app.tool()
async def get_compiler_info() -> Dict[str, Any]:
    """
    Get information about the GnuCOBOL compiler installation.

    Returns version information, configuration, and available features of the
    installed GnuCOBOL compiler.

    Returns:
        Dictionary containing:
            - available: Whether cobc is installed
            - version: Compiler version string
            - config: Configuration information
            - path: Path to cobc executable

    Example:
        >>> info = await get_compiler_info()
        >>> print(info['version'])
    """
    try:
        if not check_cobc_available():
            return {
                "available": False,
                "message": "GnuCOBOL compiler (cobc) not found in PATH",
                "installation_help": "Install from https://gnucobol.sourceforge.io/"
            }

        # Get compiler version
        version_result = await run_cobc_command(["--version"])

        # Get compiler info/config
        info_result = await run_cobc_command(["--info"])

        # Get compiler path
        compiler_path = shutil.which("cobc")

        return {
            "available": True,
            "version": version_result["stdout"].strip(),
            "config": info_result["stdout"].strip(),
            "path": compiler_path,
            "message": "GnuCOBOL compiler is available"
        }

    except COBOLCompilerError as e:
        return {
            "available": False,
            "error": str(e),
            "message": "Error querying compiler information"
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
            "message": "Unexpected error getting compiler info"
        }


# Health check endpoint
@app.tool()
async def health_check() -> Dict[str, Any]:
    """
    Check the health status of the MCP server and GnuCOBOL installation.

    Returns:
        Dictionary containing server status and compiler availability
    """
    compiler_available = check_cobc_available()

    return {
        "status": "healthy" if compiler_available else "degraded",
        "server": "online",
        "compiler_available": compiler_available,
        "message": "MCP server is running" + (
            "" if compiler_available else " (GnuCOBOL compiler not found)"
        )
    }
