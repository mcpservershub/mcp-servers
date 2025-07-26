#!/usr/bin/env python3
"""Test script to verify Dependency Check scanning functionality."""

import asyncio
import json
import os
import tempfile
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, 'src')

from dependency_check_mcp.models import ScanProjectArgs
from dependency_check_mcp.tools import DependencyCheckTools


async def test_scan():
    """Test scanning functionality."""
    # Create a test project with known vulnerabilities
    with tempfile.TemporaryDirectory() as tmpdir:
        test_project = Path(tmpdir) / "test_project"
        test_project.mkdir()
        
        # Create a package.json with known vulnerable dependency
        package_json = {
            "name": "test-vulnerable-app",
            "version": "1.0.0",
            "dependencies": {
                "lodash": "4.17.11",  # Known vulnerable version
                "express": "4.16.0"   # Older version with vulnerabilities
            }
        }
        
        with open(test_project / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)
        
        # Create output directory
        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir()
        output_file = output_dir / "scan_report.json"
        
        print(f"Test project created at: {test_project}")
        print(f"Output file will be: {output_file}")
        
        # Test if Dependency Check binary exists
        try:
            dc_tools = DependencyCheckTools()
            print(f"Dependency Check binary found at: {dc_tools.scanner.dc_binary}")
        except Exception as e:
            print(f"ERROR: Could not initialize scanner: {e}")
            return
        
        # Create scan arguments
        args = ScanProjectArgs(
            path=str(test_project),
            output_file=str(output_file),
            output_format="JSON",
            enable_experimental=True
        )
        
        print("\nStarting scan...")
        try:
            result = await dc_tools.scan_project(args)
            print("\nScan Result:")
            print(json.dumps(result, indent=2))
            
            # Check if output file was created
            if output_file.exists():
                print(f"\nOutput file created: {output_file}")
                print(f"Output file size: {output_file.stat().st_size} bytes")
                
                # Read and display first part of report
                with open(output_file, 'r') as f:
                    content = f.read()
                    print(f"\nFirst 500 chars of report:")
                    print(content[:500])
            else:
                print(f"\nERROR: Output file not created at {output_file}")
                
        except Exception as e:
            print(f"ERROR during scan: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_scan())