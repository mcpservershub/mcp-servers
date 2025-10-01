#!/usr/bin/env python3
"""
Test script to verify search_replace actually modifies files
"""

import sys
import os
import shutil
sys.path.insert(0, 'src')

from ast_grep_mcp.server import search, search_replace

def test_actual_replacement():
    """Test that search_replace actually modifies files."""
    print("=== Testing ACTUAL REPLACEMENT ===\n")
    
    # Create a backup of the test project
    test_project_path = "/home/santosh/mcp-servers/ast-grep/test_project"
    backup_path = "/home/santosh/mcp-servers/ast-grep/test_project_backup"
    
    # Remove existing backup if it exists
    if os.path.exists(backup_path):
        shutil.rmtree(backup_path)
    
    # Create backup
    shutil.copytree(test_project_path, backup_path)
    print("Created backup of test project")
    
    # Test 1: Count calculate_sum occurrences before replacement
    print("\n1. Searching for 'calculate_sum' before replacement:")
    result = search(test_project_path, "calculate_sum($$$)", "python")
    print(result)
    
    before_count = result.count("calculate_sum(")
    print(f"Found {before_count} occurrences of calculate_sum")
    
    # Test 2: Replace calculate_sum with add_numbers
    print("\n2. Replacing 'calculate_sum' with 'add_numbers':")
    result = search_replace(
        test_project_path, 
        "calculate_sum($$$)", 
        "python", 
        "add_numbers($$$)"
    )
    print(result)
    
    # Test 3: Search for calculate_sum after replacement (should be 0)
    print("\n3. Searching for 'calculate_sum' after replacement:")
    result = search(test_project_path, "calculate_sum($$$)", "python")
    print(result)
    
    # Test 4: Search for add_numbers after replacement
    print("\n4. Searching for 'add_numbers' after replacement:")
    result = search(test_project_path, "add_numbers($$$)", "python")
    print(result)
    
    after_count = result.count("add_numbers(")
    print(f"Found {after_count} occurrences of add_numbers")
    
    # Test 5: Verify the replacement worked
    if before_count > 0 and after_count == before_count:
        print(f"\n✅ SUCCESS: All {before_count} occurrences were replaced!")
    else:
        print(f"\n❌ FAILURE: Expected {before_count} replacements, got {after_count}")
    
    # Test 6: Test JavaScript replacement
    print("\n5. Testing JavaScript replacement:")
    print("Searching for 'calculateSum' in JavaScript before replacement:")
    result = search(test_project_path, "calculateSum($$$)", "javascript")
    print(result)
    
    js_before_count = result.count("calculateSum(")
    print(f"Found {js_before_count} occurrences of calculateSum")
    
    print("\nReplacing 'calculateSum' with 'addNumbers' in JavaScript:")
    result = search_replace(
        test_project_path, 
        "calculateSum($$$)", 
        "javascript", 
        "addNumbers($$$)"
    )
    print(result)
    
    print("\nSearching for 'addNumbers' after replacement:")
    result = search(test_project_path, "addNumbers($$$)", "javascript")
    print(result)
    
    js_after_count = result.count("addNumbers(")
    print(f"Found {js_after_count} occurrences of addNumbers")
    
    if js_before_count > 0 and js_after_count == js_before_count:
        print(f"\n✅ SUCCESS: All {js_before_count} JavaScript occurrences were replaced!")
    else:
        print(f"\n❌ FAILURE: Expected {js_before_count} JS replacements, got {js_after_count}")
    
    # Restore from backup
    print("\n6. Restoring files from backup...")
    if os.path.exists(test_project_path):
        shutil.rmtree(test_project_path)
    shutil.copytree(backup_path, test_project_path)
    print("Files restored from backup")

if __name__ == "__main__":
    test_actual_replacement()