#!/usr/bin/env python3.12
"""MCP Server for working with Makefiles using make CLI."""

import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import FastMCP

mcp = FastMCP("makefile-mcp")


async def run_make_command(
    args: List[str], 
    working_dir: Optional[str] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """Execute make command with given arguments."""
    try:
        cmd = ["make"] + args
        
        if working_dir:
            work_path = Path(working_dir).resolve()
            if not work_path.exists():
                return {
                    "success": False,
                    "error": f"Directory does not exist: {working_dir}",
                    "stdout": "",
                    "stderr": ""
                }
        else:
            work_path = Path.cwd()
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(work_path)
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), 
                timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds",
                "stdout": "",
                "stderr": ""
            }
        
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "return_code": proc.returncode
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "stdout": "",
            "stderr": ""
        }


def parse_targets_from_output(output: str) -> List[Dict[str, Any]]:
    """Parse targets from make -pnrR output."""
    targets = []
    seen = set()
    phony_targets = set()
    
    lines = output.split('\n')
    
    # First pass: find .PHONY targets
    for line in lines:
        if '.PHONY:' in line or '.PHONY' in line:
            parts = line.split(':', 1)
            if len(parts) > 1:
                phony_list = parts[1].strip()
                phony_targets.update(phony_list.split())
    
    # Second pass: find actual targets in Files section
    in_files_section = False
    for i, line in enumerate(lines):
        # Look for the "# Files" section
        if line.strip() == "# Files":
            in_files_section = True
            continue
        
        # Look for end of Files section
        if in_files_section and line.strip().startswith("# files hash-table"):
            break
            
        # Parse targets in Files section
        if in_files_section and ':' in line and not line.startswith('#') and not line.startswith('\t'):
            # Skip pattern rules and special targets
            if '%' in line.split(':')[0]:
                continue
                
            match = re.match(r'^([^:\s]+)\s*:\s*(.*?)$', line)
            if match:
                target_name = match.group(1)
                deps_str = match.group(2).strip()
                
                # Skip if already seen or is a special target starting with dot
                if target_name in seen or (target_name.startswith('.') and target_name != '.PHONY'):
                    continue
                    
                seen.add(target_name)
                
                # Parse dependencies
                deps = []
                if deps_str:
                    deps = [d.strip() for d in deps_str.split() if d.strip()]
                
                # Check if it's a phony target
                is_phony = target_name in phony_targets
                
                targets.append({
                    "name": target_name,
                    "dependencies": deps,
                    "phony": is_phony
                })
    
    return targets


@mcp.tool()
async def list_targets(
    working_dir: Optional[str] = None,
    makefile: Optional[str] = None,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    List all available targets in a Makefile.
    
    Args:
        working_dir: Directory containing the Makefile (default: current directory)
        makefile: Name of the Makefile (default: Makefile)
        output_file: Optional file path to write the output as JSON
    
    Returns:
        Dictionary with targets list and metadata
    """
    args = ["-pnrR"]
    
    if makefile:
        args.extend(["-f", makefile])
    
    result = await run_make_command(args, working_dir)
    
    if not result["success"]:
        if "No rule to make target" in result["stderr"] or "No targets" in result["stderr"]:
            return {
                "success": True,
                "targets": [],
                "message": "No targets found in Makefile"
            }
        return result
    
    targets = parse_targets_from_output(result["stdout"])
    
    default_target = None
    if targets:
        default_target = targets[0]["name"]
    
    result_data = {
        "success": True,
        "targets": targets,
        "default_target": default_target,
        "total_count": len(targets)
    }
    
    # Write to file if requested
    if output_file:
        try:
            output_path = Path(output_file).resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(result_data, f, indent=2)
            result_data["output_written_to"] = str(output_path)
        except Exception as e:
            result_data["output_file_error"] = f"Failed to write output file: {str(e)}"
    
    return result_data


@mcp.tool()
async def execute_target(
    target: str,
    working_dir: Optional[str] = None,
    makefile: Optional[str] = None,
    variables: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
    parallel: Optional[int] = None,
    always_make: bool = False,
    keep_going: bool = False,
    silent: bool = False
) -> Dict[str, Any]:
    """
    Execute a specific make target.
    
    Args:
        target: Target name to execute
        working_dir: Directory containing the Makefile
        makefile: Name of the Makefile
        variables: Dictionary of variables to pass (KEY=value)
        dry_run: Show commands without executing
        parallel: Number of parallel jobs
        always_make: Unconditionally make all targets
        keep_going: Continue after errors
        silent: Don't echo commands
    
    Returns:
        Execution result with output
    """
    if not target:
        return {
            "success": False,
            "error": "Target name is required"
        }
    
    args = []
    
    if makefile:
        args.extend(["-f", makefile])
    
    if dry_run:
        args.append("-n")
    
    if parallel and parallel > 1:
        args.extend(["-j", str(parallel)])
    
    if always_make:
        args.append("-B")
    
    if keep_going:
        args.append("-k")
    
    if silent:
        args.append("-s")
    
    if variables:
        for key, value in variables.items():
            args.append(f"{key}={value}")
    
    args.append(target)
    
    result = await run_make_command(args, working_dir, timeout=60)
    
    return {
        "success": result["success"],
        "target": target,
        "dry_run": dry_run,
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
        "error": result.get("error"),
        "return_code": result.get("return_code")
    }


@mcp.tool()
async def analyze_dependencies(
    target: Optional[str] = None,
    working_dir: Optional[str] = None,
    makefile: Optional[str] = None,
    show_all: bool = False,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze dependencies for targets in a Makefile.
    
    Args:
        target: Specific target to analyze (default: all targets)
        working_dir: Directory containing the Makefile
        makefile: Name of the Makefile
        show_all: Include automatic variables and built-in rules
        output_file: Optional file path to write the output as JSON
    
    Returns:
        Dependency analysis results
    """
    args = ["-pnrR"]
    
    if makefile:
        args.extend(["-f", makefile])
    
    if target:
        args.append(target)
    
    result = await run_make_command(args, working_dir)
    
    if not result["success"]:
        return result
    
    output = result["stdout"]
    targets = parse_targets_from_output(output)
    
    if target:
        targets = [t for t in targets if t["name"] == target]
        if not targets:
            return {
                "success": False,
                "error": f"Target '{target}' not found"
            }
    
    dep_tree = {}
    for t in targets:
        dep_tree[t["name"]] = {
            "direct_dependencies": t["dependencies"],
            "is_phony": t["phony"]
        }
    
    def get_all_deps(target_name, visited=None):
        if visited is None:
            visited = set()
        if target_name in visited:
            return []
        visited.add(target_name)
        
        all_deps = []
        if target_name in dep_tree:
            for dep in dep_tree[target_name]["direct_dependencies"]:
                all_deps.append(dep)
                all_deps.extend(get_all_deps(dep, visited))
        return all_deps
    
    for t_name in dep_tree:
        all_dependencies = get_all_deps(t_name)
        dep_tree[t_name]["all_dependencies"] = list(dict.fromkeys(all_dependencies))
        dep_tree[t_name]["dependency_count"] = len(dep_tree[t_name]["all_dependencies"])
    
    circular = []
    for t_name in dep_tree:
        if t_name in dep_tree[t_name]["all_dependencies"]:
            circular.append(t_name)
    
    result_data = {
        "success": True,
        "dependency_tree": dep_tree,
        "total_targets": len(dep_tree),
        "circular_dependencies": circular,
        "has_circular": len(circular) > 0
    }
    
    # Write to file if requested
    if output_file:
        try:
            output_path = Path(output_file).resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(result_data, f, indent=2)
            result_data["output_written_to"] = str(output_path)
        except Exception as e:
            result_data["output_file_error"] = f"Failed to write output file: {str(e)}"
    
    return result_data


@mcp.tool()
async def dry_run(
    target: Optional[str] = None,
    working_dir: Optional[str] = None,
    makefile: Optional[str] = None,
    variables: Optional[Dict[str, str]] = None,
    debug: bool = False,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform a dry run to see what commands would be executed.
    
    Args:
        target: Target to dry run (default: default target)
        working_dir: Directory containing the Makefile
        makefile: Name of the Makefile
        variables: Dictionary of variables to pass
        debug: Enable debug output
        output_file: Optional file path to write the output as JSON
    
    Returns:
        Commands that would be executed
    """
    args = ["-n"]
    
    if makefile:
        args.extend(["-f", makefile])
    
    if debug:
        args.append("-d")
    
    if variables:
        for key, value in variables.items():
            args.append(f"{key}={value}")
    
    if target:
        args.append(target)
    
    result = await run_make_command(args, working_dir, timeout=30)
    
    commands = []
    if result["success"]:
        lines = result["stdout"].split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('make'):
                commands.append(line)
    
    result_data = {
        "success": result["success"],
        "target": target or "default",
        "commands": commands,
        "command_count": len(commands),
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
        "error": result.get("error"),
        "debug_enabled": debug
    }
    
    # Write to file if requested
    if output_file:
        try:
            output_path = Path(output_file).resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            # For dry run, save a simplified version without stdout/stderr
            save_data = {
                "success": result_data["success"],
                "target": result_data["target"],
                "commands": result_data["commands"],
                "command_count": result_data["command_count"],
                "debug_enabled": result_data["debug_enabled"]
            }
            with open(output_path, 'w') as f:
                json.dump(save_data, f, indent=2)
            result_data["output_written_to"] = str(output_path)
        except Exception as e:
            result_data["output_file_error"] = f"Failed to write output file: {str(e)}"
    
    return result_data


@mcp.tool()
async def show_variables(
    working_dir: Optional[str] = None,
    makefile: Optional[str] = None,
    pattern: Optional[str] = None,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Display all variables defined in the Makefile.
    
    Args:
        working_dir: Directory containing the Makefile
        makefile: Name of the Makefile
        pattern: Filter variables by pattern (regex)
        output_file: Optional file path to write the output as JSON
    
    Returns:
        Dictionary of variables and their values
    """
    args = ["-pnrR"]
    
    if makefile:
        args.extend(["-f", makefile])
    
    result = await run_make_command(args, working_dir)
    
    if not result["success"]:
        return result
    
    variables = {}
    lines = result["stdout"].split('\n')
    
    # Parse variables from make database output
    for line in lines:
        # Skip comments and empty lines
        if line.startswith('#') or not line.strip():
            continue
            
        # Look for variable definitions in various forms
        # Format: "# makefile (from 'Makefile', line X)"  followed by "VAR = value"
        # Or direct format: "VAR = value"
        if '=' in line and not line.startswith('\t'):
            # Parse different variable assignment types
            match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*[:?+]?=\s*(.*)$', line)
            if match:
                var_name = match.group(1)
                var_value = match.group(2).strip()
                
                # Apply pattern filter if provided
                if pattern:
                    if not re.search(pattern, var_name):
                        continue
                
                # Skip internal make variables
                if not var_name.startswith('MAKE') and not var_name.startswith('.'):
                    variables[var_name] = var_value
    
    user_vars = {k: v for k, v in variables.items() 
                 if not k.startswith('.') and k not in ['SHELL', 'CURDIR', 'MAKEFILE_LIST']}
    
    result_data = {
        "success": True,
        "variables": user_vars,
        "total_count": len(user_vars),
        "pattern": pattern
    }
    
    # Write to file if requested
    if output_file:
        try:
            output_path = Path(output_file).resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(result_data, f, indent=2)
            result_data["output_written_to"] = str(output_path)
        except Exception as e:
            result_data["output_file_error"] = f"Failed to write output file: {str(e)}"
    
    return result_data


@mcp.tool()
async def validate_makefile(
    working_dir: Optional[str] = None,
    makefile: Optional[str] = None,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate a Makefile for syntax errors and common issues.
    
    Args:
        working_dir: Directory containing the Makefile
        makefile: Name of the Makefile (default: Makefile)
        output_file: Optional file path to write the output as JSON
    
    Returns:
        Validation results with any errors or warnings
    """
    if working_dir:
        work_path = Path(working_dir).resolve()
    else:
        work_path = Path.cwd()
    
    if makefile:
        makefile_path = work_path / makefile
    else:
        makefile_path = work_path / "Makefile"
        if not makefile_path.exists():
            makefile_path = work_path / "makefile"
    
    if not makefile_path.exists():
        return {
            "success": False,
            "error": f"Makefile not found: {makefile_path}",
            "valid": False
        }
    
    try:
        content = makefile_path.read_text()
    except Exception as e:
        return {
            "success": False,
            "error": f"Cannot read Makefile: {str(e)}",
            "valid": False
        }
    
    issues = []
    warnings = []
    
    lines = content.split('\n')
    targets_found = set()
    phony_targets = set()
    
    for i, line in enumerate(lines, 1):
        if line.startswith(' ') and '\t' not in line and ':' not in line:
            warnings.append({
                "line": i,
                "type": "warning",
                "message": "Recipe lines should start with tab, not spaces"
            })
        
        if line.strip().startswith('.PHONY:'):
            phony_list = line.split(':', 1)[1].strip()
            phony_targets.update(phony_list.split())
        
        match = re.match(r'^([^:\s]+)\s*:', line)
        if match:
            target = match.group(1)
            if not target.startswith('.'):
                targets_found.add(target)
    
    common_phony = {'clean', 'all', 'install', 'test', 'help'}
    missing_phony = (targets_found & common_phony) - phony_targets
    for target in missing_phony:
        warnings.append({
            "type": "warning",
            "message": f"Target '{target}' should probably be .PHONY"
        })
    
    args = ["-n", "--warn-undefined-variables"]
    if makefile:
        args.extend(["-f", makefile])
    
    result = await run_make_command(args, working_dir)
    
    if "missing separator" in result.get("stderr", ""):
        issues.append({
            "type": "error",
            "message": "Syntax error: missing separator (did you mean TAB instead of spaces?)"
        })
    
    if "*** No targets" in result.get("stderr", ""):
        issues.append({
            "type": "error",
            "message": "No targets defined in Makefile"
        })
    
    valid = len(issues) == 0
    
    result_data = {
        "success": True,
        "valid": valid,
        "errors": issues,
        "warnings": warnings,
        "error_count": len(issues),
        "warning_count": len(warnings),
        "targets_found": len(targets_found),
        "message": "Makefile is valid" if valid else "Makefile has errors"
    }
    
    # Write to file if requested
    if output_file:
        try:
            output_path = Path(output_file).resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(result_data, f, indent=2)
            result_data["output_written_to"] = str(output_path)
        except Exception as e:
            result_data["output_file_error"] = f"Failed to write output file: {str(e)}"
    
    return result_data


@mcp.tool()
async def clean_build(
    working_dir: Optional[str] = None,
    makefile: Optional[str] = None,
    target: str = "clean"
) -> Dict[str, Any]:
    """
    Execute clean target to remove build artifacts.
    
    Args:
        working_dir: Directory containing the Makefile
        makefile: Name of the Makefile
        target: Clean target name (default: clean)
    
    Returns:
        Clean operation result
    """
    return await execute_target(
        target=target,
        working_dir=working_dir,
        makefile=makefile,
        silent=False
    )


def main():
    """Main entry point for the MCP server."""
    import sys
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()