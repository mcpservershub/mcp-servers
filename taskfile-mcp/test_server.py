#!/usr/bin/env python3.12
"""Test script for the Taskfile MCP Server."""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent))

from src.server import (
    list_tasks, run_task, init_taskfile, validate_taskfile,
    get_task_summary, dry_run, watch_task,
    ListTasksInput, RunTaskInput, InitTaskfileInput,
    ValidateTaskfileInput, SummaryInput
)


async def test_all_tools():
    """Test all MCP tools."""
    print("Testing Taskfile MCP Server\n")
    print("=" * 50)
    
    # Test 1: Initialize a Taskfile
    print("\n1. Testing init_taskfile...")
    try:
        import tempfile
        test_dir = Path(tempfile.mkdtemp(prefix="taskfile_test_"))
        
        result = await init_taskfile(InitTaskfileInput(
            working_dir=str(test_dir)
        ))
        if result["success"]:
            print(f"✓ Initialized Taskfile in {test_dir}")
        else:
            print(f"✗ Failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: Validate the Taskfile
    print("\n2. Testing validate_taskfile...")
    try:
        result = await validate_taskfile(ValidateTaskfileInput(
            working_dir=str(test_dir)
        ))
        if result["success"]:
            if result["valid"]:
                print(f"✓ Taskfile is valid")
            else:
                print(f"✗ Taskfile is invalid: {result.get('error', '')}")
        else:
            print(f"✗ Failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 3: List tasks
    print("\n3. Testing list_tasks...")
    try:
        result = await list_tasks(ListTasksInput(
            working_dir=str(test_dir),
            json_output=True
        ))
        if result["success"]:
            tasks_data = result.get("tasks", {})
            if isinstance(tasks_data, dict) and "tasks" in tasks_data:
                print(f"✓ Listed {len(tasks_data['tasks'])} tasks")
                for task in tasks_data["tasks"][:3]:
                    print(f"  - {task.get('name', 'unknown')}")
            else:
                print(f"✓ Got response")
        else:
            print(f"✗ Failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 4: Dry run
    print("\n4. Testing dry_run...")
    try:
        result = await dry_run(RunTaskInput(
            task_name="default",
            working_dir=str(test_dir)
        ))
        if result["success"]:
            print(f"✓ Dry run completed")
        else:
            print(f"✗ Failed with return code {result.get('returncode', -1)}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 5: Get task summary
    print("\n5. Testing get_task_summary...")
    try:
        result = await get_task_summary(SummaryInput(
            task_name="default",
            working_dir=str(test_dir)
        ))
        if result["success"]:
            print(f"✓ Got summary for 'default' task")
        else:
            print(f"✗ Failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Cleanup
    print("\n" + "=" * 50)
    print("Cleaning up...")
    try:
        import shutil
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print(f"✓ Removed test directory")
    except Exception as e:
        print(f"✗ Could not clean up: {e}")
    
    print("\nTest complete!")


if __name__ == "__main__":
    print("Taskfile MCP Server Test Suite")
    print("==============================")
    
    import shutil
    if not shutil.which("task"):
        print("\n⚠️  WARNING: Task CLI not found!")
        print("Please install it from: https://taskfile.dev/installation")
        print("\nTests will fail without Task CLI.\n")
    
    asyncio.run(test_all_tools())