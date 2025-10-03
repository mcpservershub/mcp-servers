#!/usr/bin/env python3
"""Simple test script for MCP tools"""
import sys
import json

sys.path.insert(0, '/app/src')
from skim_mcp_server.server import (
    check_sk_installed,
    fuzzy_filter_lines,
    fuzzy_find_files,
    fuzzy_search_content,
    fuzzy_select_git_files,
    interactive_search
)

print("=" * 60)
print("Skim MCP Server - Tool Tests")
print("=" * 60)
print()

# Test 1: Check sk installation
print("Test 1: Check sk installation")
print("-" * 40)
sk_installed = check_sk_installed()
print(f"✓ sk installed: {sk_installed}")
print()

# Test 2: fuzzy_filter_lines
print("Test 2: fuzzy_filter_lines")
print("-" * 40)
result = fuzzy_filter_lines(
    input_text="apple\nbanana\ncherry\napricot\navocado",
    query="",
    multi=False
)
print(f"Success: {result['success']}")
print(f"Exit code: {result['exit_code']}")
print(f"Error: {result.get('error', 'None')}")
print()

# Test 3: fuzzy_find_files
print("Test 3: fuzzy_find_files")
print("-" * 40)
result = fuzzy_find_files(
    directory="/workspace",
    query="",
    preview=False,
    multi=False
)
print(f"Success: {result['success']}")
print(f"Exit code: {result['exit_code']}")
print(f"Error: {result.get('error', 'None')}")
print()

# Test 4: fuzzy_search_content
print("Test 4: fuzzy_search_content")
print("-" * 40)
result = fuzzy_search_content(
    directory="/workspace",
    query="",
    preview=False,
    multi=False
)
print(f"Success: {result['success']}")
print(f"Exit code: {result['exit_code']}")
print(f"Error: {result.get('error', 'None')}")
print()

# Test 5: List available dependencies
print("Test 5: Tool dependencies")
print("-" * 40)
import shutil
tools = {
    'sk': shutil.which('sk'),
    'fd': shutil.which('fd'),
    'rg': shutil.which('rg'),
    'bat': shutil.which('bat'),
    'git': shutil.which('git')
}
for tool, path in tools.items():
    status = "✓" if path else "✗"
    print(f"{status} {tool}: {path or 'not found'}")
print()

print("=" * 60)
print("All tests completed!")
print("=" * 60)
