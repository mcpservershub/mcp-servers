#!/usr/bin/env python3.12
"""Test the output_file feature of list_tasks."""

import asyncio
import json
from pathlib import Path
from src.server import list_tasks


async def test_output_file():
    """Test saving list_tasks output to file."""
    print("Testing output_file feature\n" + "=" * 50)
    
    # Test 1: Save JSON output to file
    print("\n1. Save JSON output to file:")
    result = await list_tasks(
        working_dir="/home/santosh/compare/taskfile-mcp/examples",
        taskfile="simple-python.yml",
        json_output=True,
        output_file="tasks_output.json"
    )
    print(f"   Success: {result['success']}")
    if result.get('output_file'):
        print(f"   Saved to: {result['output_file']}")
        print(f"   Message: {result.get('message', '')}")
    
    # Test 2: Save text output to file
    print("\n2. Save text output to file:")
    result = await list_tasks(
        working_dir="/home/santosh/compare/taskfile-mcp/examples",
        taskfile="simple-python.yml",
        json_output=False,
        output_file="tasks_output.txt"
    )
    print(f"   Success: {result['success']}")
    if result.get('output_file'):
        print(f"   Saved to: {result['output_file']}")
    
    # Test 3: Save with absolute path
    print("\n3. Save with absolute path:")
    result = await list_tasks(
        working_dir="/home/santosh/compare/taskfile-mcp/examples",
        taskfile="simple-go.yml",
        json_output=True,
        output_file="/tmp/go_tasks.json"
    )
    print(f"   Success: {result['success']}")
    if result.get('output_file'):
        print(f"   Saved to: {result['output_file']}")
    
    # Test 4: Verify file contents
    print("\n4. Verify saved files:")
    
    # Check JSON file
    json_file = Path("/home/santosh/compare/taskfile-mcp/examples/tasks_output.json")
    if json_file.exists():
        with open(json_file) as f:
            data = json.load(f)
            print(f"   JSON file has {len(data.get('tasks', []))} tasks")
    
    # Check text file
    text_file = Path("/home/santosh/compare/taskfile-mcp/examples/tasks_output.txt")
    if text_file.exists():
        content = text_file.read_text()
        print(f"   Text file size: {len(content)} bytes")
    
    # Check absolute path file
    abs_file = Path("/tmp/go_tasks.json")
    if abs_file.exists():
        with open(abs_file) as f:
            data = json.load(f)
            print(f"   Absolute path file has {len(data.get('tasks', []))} tasks")
    
    print("\n" + "=" * 50)
    print("Test complete!")


if __name__ == "__main__":
    asyncio.run(test_output_file())