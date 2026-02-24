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


def parse_call_statements(listing: str, source_code: str) -> List[Dict[str, Any]]:
    """
    Parse CALL statements from COBOL listing and source code.

    Extracts external program calls from the source code.

    Args:
        listing: GnuCOBOL listing output
        source_code: Original COBOL source code

    Returns:
        List of dictionaries containing call information
    """
    import re

    calls = []

    # Pattern to match CALL statements in COBOL
    # Matches: CALL 'PROGRAM-NAME' or CALL "PROGRAM-NAME" or CALL IDENTIFIER
    call_pattern = r"CALL\s+['\"]([A-Z0-9\-_]+)['\"]"

    for match in re.finditer(call_pattern, source_code, re.IGNORECASE):
        program_name = match.group(1)
        calls.append({
            "program": program_name,
            "type": "external_call"
        })

    return calls


def parse_copy_statements(listing: str, source_code: str) -> List[Dict[str, Any]]:
    """
    Parse COPY statements from COBOL listing and source code.

    Extracts copybook dependencies from the source code.

    Args:
        listing: GnuCOBOL listing output
        source_code: Original COBOL source code

    Returns:
        List of dictionaries containing copy information
    """
    import re

    copies = []

    # Pattern to match COPY statements in COBOL
    # Matches: COPY 'COPYBOOK' or COPY "COPYBOOK" or COPY COPYBOOK
    copy_pattern = r"COPY\s+(?:['\"]([A-Z0-9\-_\.]+)['\"]|([A-Z0-9\-_\.]+))"

    for match in re.finditer(copy_pattern, source_code, re.IGNORECASE):
        copybook_name = match.group(1) or match.group(2)
        copies.append({
            "copybook": copybook_name,
            "type": "include"
        })

    return copies


def extract_program_id(source_code: str) -> Optional[str]:
    """
    Extract PROGRAM-ID from COBOL source code.

    Args:
        source_code: COBOL source code

    Returns:
        Program ID if found, None otherwise
    """
    import re

    # Pattern to match PROGRAM-ID
    program_id_pattern = r"PROGRAM-ID\.\s+([A-Z0-9\-_]+)"

    match = re.search(program_id_pattern, source_code, re.IGNORECASE)
    if match:
        return match.group(1)

    return None


def discover_cobol_files(directory_path: str, recursive: bool = True) -> List[str]:
    """
    Discover COBOL source files in a directory.

    Looks for files with common COBOL extensions:
    - .cob, .cbl, .COB, .CBL (standard COBOL)
    - .c74, .C74 (COBOL 74)
    - .c85, .C85 (COBOL 85)
    - .cpy, .CPY (copybooks - sometimes used for source)
    - .pco, .PCO (Pro*COBOL)
    - .sqb, .SQB (SQL embedded COBOL)

    Args:
        directory_path: Path to directory to search
        recursive: Whether to search subdirectories recursively

    Returns:
        List of absolute paths to COBOL files found
    """
    cobol_extensions = {
        '.cob', '.cbl', '.COB', '.CBL',  # Standard COBOL
        '.c74', '.C74',                    # COBOL 74
        '.c85', '.C85',                    # COBOL 85
        '.cpy', '.CPY',                    # Copybooks (sometimes source files)
        '.pco', '.PCO',                    # Pro*COBOL
        '.sqb', '.SQB'                     # SQL embedded COBOL
    }
    cobol_files = []

    dir_path = Path(directory_path)

    if not dir_path.exists():
        return []

    if not dir_path.is_dir():
        return []

    # Use glob to find files
    if recursive:
        # Recursively search all subdirectories
        for ext in cobol_extensions:
            cobol_files.extend(dir_path.rglob(f'*{ext}'))
    else:
        # Only search immediate directory
        for ext in cobol_extensions:
            cobol_files.extend(dir_path.glob(f'*{ext}'))

    # Convert to absolute paths and sort
    return sorted([str(f.absolute()) for f in cobol_files])


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
    copybook_paths: Optional[List[str]] = None,
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

            # Add copybook search paths (-I flags)
            if copybook_paths:
                for path in copybook_paths:
                    analyze_args.extend(["-I", path])

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
    copybook_paths: Optional[List[str]] = None,
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
        copybook_paths: List of directories to search for COPY files (adds -I flags)
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
            copybook_paths=copybook_paths,
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
async def compile_project(
    directory: str,
    output_name: str,
    output_type: str = "executable",
    copybook_paths: Optional[List[str]] = None,
    library_paths: Optional[List[str]] = None,
    recursive: bool = True,
    options: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Compile an entire COBOL project from a directory into a single output.

    This tool discovers all COBOL files in a directory and compiles them together
    using GnuCOBOL's project compilation features (cobc -b or cobc -x).
    This is more efficient than compiling files individually and properly handles
    inter-file dependencies.

    Args:
        directory: Directory path containing COBOL source files
        output_name: Name for the output file (executable or module)
        output_type: Type of output - "executable" (-x) or "module" (-b for shared library)
        copybook_paths: List of directories to search for COPY files (adds -I flags)
        library_paths: List of directories to search for libraries (adds -L flags)
        recursive: Search subdirectories recursively for COBOL files (default: True)
        options: Additional compiler options (e.g., ["-Wall", "-O2"])

    Returns:
        Dictionary containing:
            - success: Whether compilation succeeded
            - directory: Source directory that was compiled
            - output_name: Name of the compiled output
            - output_type: Type of output (executable or module)
            - files_compiled: Number of COBOL files included
            - file_list: List of files that were compiled
            - stdout: Compiler standard output
            - stderr: Compiler standard error
            - return_code: Compiler exit code

    Example:
        >>> result = await compile_project(
        ...     directory="/workspace/cobol-app",
        ...     output_name="myapp",
        ...     output_type="executable",
        ...     copybook_paths=["/workspace/cobol-app/copybooks"],
        ...     recursive=True
        ... )
    """
    try:
        # Validate output type
        if output_type not in ["executable", "module"]:
            return {
                "success": False,
                "error": "output_type must be 'executable' or 'module'",
                "message": "Invalid output type"
            }

        # Discover COBOL files
        cobol_files = discover_cobol_files(directory, recursive=recursive)

        if not cobol_files:
            return {
                "success": False,
                "error": f"No COBOL files found in directory: {directory}",
                "message": "No COBOL files (.cob, .cbl, .COB, .CBL) found"
            }

        if len(cobol_files) > 100:
            return {
                "success": False,
                "error": f"Too many files ({len(cobol_files)}). Maximum 100 files per project compilation.",
                "message": "Project too large for single compilation"
            }

        # Create temporary directory for output
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_file = temp_path / output_name

            # Build compiler arguments
            compile_args = []

            # Add output type flag
            if output_type == "executable":
                compile_args.append("-x")  # Build executable
            else:
                compile_args.append("-b")  # Build module/library

            # Add output file
            compile_args.extend(["-o", str(output_file)])

            # Add copybook search paths (-I flags)
            if copybook_paths:
                for path in copybook_paths:
                    compile_args.extend(["-I", path])

            # Add library search paths (-L flags)
            if library_paths:
                for path in library_paths:
                    compile_args.extend(["-L", path])

            # Add user-provided options
            if options:
                compile_args.extend(options)

            # Add all COBOL source files
            compile_args.extend(cobol_files)

            # Run compilation
            result = await run_cobc_command(compile_args, timeout=120)  # Longer timeout for projects

            success = result["return_code"] == 0

            response = {
                "success": success,
                "directory": str(Path(directory).absolute()),
                "output_name": output_name,
                "output_type": output_type,
                "files_compiled": len(cobol_files),
                "file_list": cobol_files,
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "return_code": result["return_code"],
                "command": result["command"]
            }

            if success:
                response["message"] = f"Successfully compiled {len(cobol_files)} files into {output_type}: {output_name}"
            else:
                response["message"] = f"Project compilation failed"
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
            "message": "Unexpected error during project compilation"
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


@app.tool()
async def batch_analyze(
    file_paths: Optional[List[str]] = None,
    directory: Optional[str] = None,
    recursive: bool = True,
    copybook_paths: Optional[List[str]] = None,
    include_symbols: bool = True,
    include_xref: bool = True
) -> Dict[str, Any]:
    """
    Analyze multiple COBOL source files and extract project-level semantic relationships.

    This tool runs GnuCOBOL analysis on each file, then aggregates the results to show:
    - Program call relationships (which programs call which)
    - Copybook dependencies (which files use which copybooks)
    - Program-level summary

    This provides project-level semantic analysis by leveraging GnuCOBOL's
    per-file analysis capabilities.

    You can either provide a list of specific file paths OR a directory to scan.
    If directory is provided, it will automatically discover COBOL files (.cob, .cbl, .COB, .CBL).

    Args:
        file_paths: List of paths to COBOL source files (optional if directory is provided)
        directory: Directory path to scan for COBOL files (optional if file_paths is provided)
        recursive: When using directory, search subdirectories recursively (default: True)
        copybook_paths: List of directories to search for COPY files (adds -I flags)
        include_symbols: Include symbol tables in individual file analysis
        include_xref: Include cross-reference in individual file analysis

    Returns:
        Dictionary containing:
            - total_files: Number of files analyzed
            - program_calls: Map of programs and what they call
            - copybook_usage: Map of programs and copybooks they use
            - programs: List of program IDs found
            - per_file_analysis: Detailed analysis for each file
            - call_summary: Summary of all external calls found
            - copybook_summary: Summary of all copybooks referenced

    Example with file_paths:
        >>> result = await batch_analyze(
        ...     file_paths=[
        ...         "/workspace/src/MAIN.COB",
        ...         "/workspace/src/CUSTOMER.COB"
        ...     ]
        ... )

    Example with directory:
        >>> result = await batch_analyze(
        ...     directory="/workspace/src",
        ...     recursive=True
        ... )
    """
    try:
        # Determine file list from either file_paths or directory
        if directory:
            # Use directory discovery
            discovered_files = discover_cobol_files(directory, recursive=recursive)
            if not discovered_files:
                return {
                    "total_files": 0,
                    "error": f"No COBOL files found in directory: {directory}",
                    "message": "No COBOL files (.cob, .cbl, .COB, .CBL) found in the specified directory"
                }
            file_paths = discovered_files
        elif file_paths:
            # Use provided file_paths
            if not isinstance(file_paths, list):
                raise ValueError("file_paths must be a list")
        else:
            raise ValueError("Either file_paths or directory must be provided")

        if len(file_paths) > 50:
            raise ValueError("Maximum 50 files allowed per batch analysis")

        # Initialize result structures
        program_calls = {}
        copybook_usage = {}
        programs = []
        per_file_analysis = {}
        all_calls = []
        all_copybooks = []

        # Analyze each file
        for file_path in file_paths:
            try:
                # Validate file path
                source_path = Path(file_path)

                if not source_path.exists():
                    per_file_analysis[file_path] = {
                        "success": False,
                        "error": "File not found"
                    }
                    continue

                if not source_path.is_file():
                    per_file_analysis[file_path] = {
                        "success": False,
                        "error": "Not a file"
                    }
                    continue

                # Read source code
                try:
                    code = source_path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    per_file_analysis[file_path] = {
                        "success": False,
                        "error": "File encoding error"
                    }
                    continue

                # Extract program ID
                program_id = extract_program_id(code)
                if program_id:
                    programs.append(program_id)

                # Run GnuCOBOL analysis
                analysis_result = await _analyze_cobol_code(
                    code=code,
                    include_symbols=include_symbols,
                    include_xref=include_xref,
                    copybook_paths=copybook_paths
                )

                # Parse CALL statements from source
                calls = parse_call_statements(
                    analysis_result.get("listing", ""),
                    code
                )

                # Parse COPY statements from source
                copies = parse_copy_statements(
                    analysis_result.get("listing", ""),
                    code
                )

                # Store per-file results
                per_file_analysis[file_path] = {
                    "success": analysis_result["success"],
                    "program_id": program_id,
                    "calls": calls,
                    "copybooks": copies,
                    "analysis_summary": {
                        "has_errors": analysis_result.get("analysis", {}).get("has_errors", False),
                        "has_warnings": analysis_result.get("analysis", {}).get("has_warnings", False)
                    }
                }

                # Aggregate project-level data
                if program_id:
                    program_calls[program_id] = [call["program"] for call in calls]
                    copybook_usage[program_id] = [copy["copybook"] for copy in copies]

                all_calls.extend(calls)
                all_copybooks.extend(copies)

            except Exception as e:
                per_file_analysis[file_path] = {
                    "success": False,
                    "error": str(e)
                }

        # Build call summary (unique programs called)
        unique_calls = {}
        for call in all_calls:
            program = call["program"]
            unique_calls[program] = unique_calls.get(program, 0) + 1

        # Build copybook summary (unique copybooks used)
        unique_copybooks = {}
        for copybook in all_copybooks:
            book = copybook["copybook"]
            unique_copybooks[book] = unique_copybooks.get(book, 0) + 1

        # Build response
        return {
            "total_files": len(file_paths),
            "programs": programs,
            "program_calls": program_calls,
            "copybook_usage": copybook_usage,
            "per_file_analysis": per_file_analysis,
            "call_summary": {
                "total_calls": len(all_calls),
                "unique_programs_called": list(unique_calls.keys()),
                "call_counts": unique_calls
            },
            "copybook_summary": {
                "total_copybooks": len(all_copybooks),
                "unique_copybooks": list(unique_copybooks.keys()),
                "usage_counts": unique_copybooks
            },
            "message": f"Analyzed {len(file_paths)} files, found {len(programs)} programs, {len(unique_calls)} unique external calls, {len(unique_copybooks)} copybooks"
        }

    except ValueError as e:
        return {
            "total_files": 0,
            "error": str(e),
            "message": "Invalid input for batch analysis"
        }
    except Exception as e:
        return {
            "total_files": 0,
            "error": str(e),
            "message": "Unexpected error during batch analysis"
        }
