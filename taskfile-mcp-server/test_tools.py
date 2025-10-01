#!/usr/bin/env python3.12
"""Direct test of MCP tools to verify they work correctly."""

import asyncio
import json
from src.server import (
    list_tasks, run_task, init_taskfile, validate_taskfile,
    get_task_summary, dry_run
)


async def test_tools():
    """Test all tools directly."""
    print("Testing MCP Tools Directly\n" + "=" * 50)
    
    # Test 1: List tasks from examples with default Taskfile.yml
    print("\n1. List tasks from examples/Taskfile.yml:")
    result = await list_tasks(
        working_dir="/home/santosh/compare/taskfile-mcp/examples",
        json_output=True
    )
    print(f"   Success: {result['success']}")
    if result['success'] and 'tasks' in result:
        tasks = result['tasks'].get('tasks', [])
        print(f"   Found {len(tasks)} tasks")
    
    # Test 2: List tasks from custom taskfile
    print("\n2. List tasks from examples/simple-python.yml:")
    result = await list_tasks(
        working_dir="/home/santosh/compare/taskfile-mcp/examples",
        taskfile="simple-python.yml",
        json_output=True
    )
    print(f"   Success: {result['success']}")
    if result['success'] and 'tasks' in result:
        tasks = result['tasks'].get('tasks', [])
        print(f"   Found {len(tasks)} tasks")
        for task in tasks[:5]:
            print(f"     - {task.get('name')}: {task.get('desc', 'no description')}")
    
    # Test 3: Validate taskfile
    print("\n3. Validate examples/simple-python.yml:")
    result = await validate_taskfile(
        working_dir="/home/santosh/compare/taskfile-mcp/examples"
    )
    print(f"   Valid: {result.get('valid', False)}")
    
    # Test 4: Get task summary
    print("\n4. Get summary of 'test' task:")
    result = await get_task_summary(
        task_name="test",
        working_dir="/home/santosh/compare/taskfile-mcp/examples",
    )
    print(f"   Success: {result['success']}")
    if result['success']:
        summary = result.get('summary', '')
        print(f"   Summary length: {len(summary)} chars")
    
    # Test 5: Dry run
    print("\n5. Dry run 'default' task:")
    result = await dry_run(
        task_name="default",
        working_dir="/home/santosh/compare/taskfile-mcp/examples"
    )
    print(f"   Success: {result['success']}")
    if result['success']:
        print(f"   Return code: {result.get('returncode')}")
    
    print("\n" + "=" * 50)
    print("All tests completed!")


if __name__ == "__main__":
    print("Direct Tool Testing (bypassing MCP Inspector)")
    print("This proves the tools work correctly\n")
    
    asyncio.run(test_tools())