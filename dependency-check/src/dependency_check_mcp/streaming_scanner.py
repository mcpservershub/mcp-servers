"""Streaming scanner implementation to handle long-running scans."""

import asyncio
import json
import time
from pathlib import Path
from typing import AsyncIterator, Dict, Any

from .scanner import DependencyCheckScanner
from .models import ScanResult


class StreamingScanner:
    """Scanner that provides progress updates to prevent timeouts."""
    
    def __init__(self, scanner: DependencyCheckScanner):
        self.scanner = scanner
        
    async def scan_with_progress(
        self,
        path: str,
        output_format: str,
        output_file: str,
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Scan with progress updates.
        
        Yields progress messages during the scan to prevent MCP timeout.
        """
        start_time = time.time()
        
        # Initial progress
        yield {
            "type": "progress",
            "message": "Starting dependency check scan...",
            "phase": "initialization",
            "elapsed": 0
        }
        
        # Check if this is first run
        data_dir = Path(self.scanner.dc_home) / "data"
        if not data_dir.exists() or not any(data_dir.iterdir()):
            yield {
                "type": "progress", 
                "message": "First run detected. Downloading vulnerability database (5-30 minutes)...",
                "phase": "database_download",
                "elapsed": time.time() - start_time
            }
        
        # Start the scan in a background task
        scan_task = asyncio.create_task(
            self.scanner.scan(
                path=path,
                output_format=output_format,
                output_file=output_file,
                **kwargs
            )
        )
        
        # Send progress updates while scan is running
        update_count = 0
        while not scan_task.done():
            await asyncio.sleep(5)  # Update every 5 seconds
            update_count += 1
            elapsed = time.time() - start_time
            
            # Different messages based on elapsed time
            if elapsed < 30:
                phase = "analyzing"
                message = f"Analyzing project structure... ({int(elapsed)}s)"
            elif elapsed < 60:
                phase = "scanning"
                message = f"Scanning dependencies... ({int(elapsed)}s)"
            elif elapsed < 120:
                phase = "checking"
                message = f"Checking vulnerability database... ({int(elapsed)}s)"
            else:
                phase = "processing"
                message = f"Processing results... ({int(elapsed)}s)"
            
            yield {
                "type": "progress",
                "message": message,
                "phase": phase,
                "elapsed": elapsed,
                "update": update_count
            }
        
        # Get the result
        try:
            result = await scan_task
            
            # Final progress
            yield {
                "type": "progress",
                "message": "Scan completed successfully",
                "phase": "completed",
                "elapsed": time.time() - start_time
            }
            
            # Return the actual result
            yield {
                "type": "result",
                "data": result.model_dump()
            }
            
        except Exception as e:
            yield {
                "type": "error",
                "message": str(e),
                "phase": "error",
                "elapsed": time.time() - start_time
            }