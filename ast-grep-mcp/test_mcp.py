#!/usr/bin/env python3
"""
Test script for the ast-grep MCP server
"""

import sys
import os
sys.path.insert(0, 'src')

from ast_grep_mcp.server import search, search_replace

def test_search_function():
    """Test the search function with various patterns."""
    print("=== Testing SEARCH function ===\n")
    
    test_project_path = "/home/santosh/mcp-servers/ast-grep/test_project"
    
    # Test 1: Search for function calls in Python
    print("1. Searching for 'calculate_sum' function calls in Python:")
    result = search(test_project_path, "calculate_sum($$$)", "python")
    print(result)
    print("\n" + "="*50 + "\n")
    
    # Test 2: Search for function definitions in Python
    print("2. Searching for function definitions in Python:")
    result = search(test_project_path, "def $FUNC($$$):", "python")
    print(result)
    print("\n" + "="*50 + "\n")
    
    # Test 3: Search for print statements in Python
    print("3. Searching for print statements in Python:")
    result = search(test_project_path, "print($$$)", "python")
    print(result)
    print("\n" + "="*50 + "\n")
    
    # Test 4: Search for function calls in JavaScript
    print("4. Searching for 'calculateSum' function calls in JavaScript:")
    result = search(test_project_path, "calculateSum($$$)", "javascript")
    print(result)
    print("\n" + "="*50 + "\n")
    
    # Test 5: Search for console.log in JavaScript
    print("5. Searching for console.log in JavaScript:")
    result = search(test_project_path, "console.log($$$)", "javascript")
    print(result)
    print("\n" + "="*50 + "\n")

def test_search_replace_function():
    """Test the search_replace function with various patterns."""
    print("=== Testing SEARCH_REPLACE function ===\n")
    
    test_project_path = "/home/santosh/mcp-servers/ast-grep/test_project"
    
    # Test 1: Replace calculate_sum with add_numbers in Python
    print("1. Replacing 'calculate_sum' with 'add_numbers' in Python:")
    result = search_replace(
        test_project_path, 
        "calculate_sum($$$)", 
        "python", 
        "add_numbers($$$)"
    )
    print(result)
    print("\n" + "="*50 + "\n")
    
    # Test 2: Replace print with log_output in Python
    print("2. Replacing 'print' with 'log_output' in Python:")
    result = search_replace(
        test_project_path, 
        "print($MSG)", 
        "python", 
        "log_output($MSG)"
    )
    print(result)
    print("\n" + "="*50 + "\n")
    
    # Test 3: Replace calculateSum with addNumbers in JavaScript
    print("3. Replacing 'calculateSum' with 'addNumbers' in JavaScript:")
    result = search_replace(
        test_project_path, 
        "calculateSum($$$)", 
        "javascript", 
        "addNumbers($$$)"
    )
    print(result)
    print("\n" + "="*50 + "\n")
    
    # Test 4: Replace console.log with logger.info in JavaScript
    print("4. Replacing 'console.log' with 'logger.info' in JavaScript:")
    result = search_replace(
        test_project_path, 
        "console.log($MSG)", 
        "javascript", 
        "logger.info($MSG)"
    )
    print(result)
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    print("Starting MCP Server Tests...\n")
    
    # Run search tests first
    test_search_function()
    
    # Run search and replace tests
    test_search_replace_function()
    
    print("Tests completed!")