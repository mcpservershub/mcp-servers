"""Wrapper for CTags operations."""

import os
import re
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
import ctags
from ctags import CTags, TagEntry

logger = logging.getLogger(__name__)


class CTagsWrapper:
    """Wrapper class for Universal CTags operations."""
    
    def __init__(self, ctags_binary: str = "ctags"):
        """Initialize CTags wrapper.
        
        Args:
            ctags_binary: Path to ctags binary
        """
        self.ctags_binary = ctags_binary
        self._verify_ctags()
    
    def _verify_ctags(self) -> None:
        """Verify ctags is installed and accessible."""
        try:
            result = subprocess.run(
                [self.ctags_binary, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError(f"CTags not found at {self.ctags_binary}")
            logger.info(f"CTags found: {result.stdout.splitlines()[0]}")
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            raise RuntimeError(f"Failed to verify ctags: {e}")
    
    def generate_tags(
        self,
        path: str,
        output_file: str = "tags",
        recursive: bool = True,
        languages: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        extra_options: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate tags file for given path.
        
        Args:
            path: Path to index
            output_file: Output tags file
            recursive: Recursive indexing
            languages: Languages to include
            exclude_patterns: Patterns to exclude
            extra_options: Extra ctags options
            
        Returns:
            Dictionary with generation results
        """
        cmd = [self.ctags_binary]
        
        # Add output file
        cmd.extend(["-f", output_file])
        
        # Add recursive flag
        if recursive:
            cmd.append("-R")
        
        # Add language filters
        if languages:
            lang_str = ",".join(languages)
            cmd.extend(["--languages=" + lang_str])
        
        # Add exclude patterns
        if exclude_patterns:
            for pattern in exclude_patterns:
                cmd.extend(["--exclude=" + pattern])
        
        # Add extra options
        if extra_options:
            cmd.extend(extra_options)
        
        # Add fields for better tag information
        cmd.extend(["--fields=+KSn", "--extras=+q"])
        
        # Add the path to index
        cmd.append(path)
        
        try:
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # Count tags generated
                tag_count = 0
                if os.path.exists(output_file):
                    with open(output_file, 'r') as f:
                        tag_count = sum(1 for line in f if not line.startswith('!'))
                
                return {
                    "success": True,
                    "tags_file": os.path.abspath(output_file),
                    "tag_count": tag_count,
                    "command": " ".join(cmd)
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr or "Failed to generate tags",
                    "command": " ".join(cmd)
                }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Tag generation timed out after 60 seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def open_tags_file(self, tags_file: str) -> Optional[CTags]:
        """Open a tags file for reading.
        
        Args:
            tags_file: Path to tags file
            
        Returns:
            CTags object or None if failed
        """
        try:
            if not os.path.exists(tags_file):
                logger.error(f"Tags file not found: {tags_file}")
                return None
            
            # python-ctags3 expects bytes for the filename
            tag_file = CTags(tags_file.encode('utf-8') if isinstance(tags_file, str) else tags_file)
            return tag_file
        except Exception as e:
            logger.error(f"Failed to open tags file: {e}")
            return None
    
    def find_symbol(
        self,
        tags_file: str,
        symbol_name: str,
        match_type: str = "exact",
        case_sensitive: bool = True,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Find symbols in tags file.
        
        Args:
            tags_file: Path to tags file
            symbol_name: Symbol to search
            match_type: Type of match (exact, partial, regex)
            case_sensitive: Case sensitive search
            limit: Maximum results
            
        Returns:
            List of matching symbols
        """
        tag_file = self.open_tags_file(tags_file)
        if not tag_file:
            return []
        
        results = []
        entry = TagEntry()
        
        # Set search options
        options = 0
        if match_type == "partial":
            options |= ctags.TAG_PARTIALMATCH
        if not case_sensitive:
            options |= ctags.TAG_IGNORECASE
        
        try:
            # For regex matching, we need to iterate through all tags
            if match_type == "regex":
                try:
                    pattern = re.compile(symbol_name, re.IGNORECASE if not case_sensitive else 0)
                except re.error as e:
                    logger.error(f"Invalid regex pattern '{symbol_name}': {e}")
                    return []
                
                success = tag_file.first(entry)
                if success:
                    count = 0
                    while True:
                        try:
                            # entry['name'] might be bytes, decode it
                            name = entry.get('name') if hasattr(entry, 'get') else entry['name']
                            if name is None:
                                logger.warning(f"Entry has no name at position {count}")
                                if not tag_file.next(entry):
                                    break
                                continue
                                
                            if isinstance(name, bytes):
                                name = name.decode('utf-8', errors='ignore')
                            
                            # Debug log first few entries
                            if count < 5:
                                logger.info(f"Regex check #{count}: '{name}' against pattern '{symbol_name}'")
                            count += 1
                            
                            if pattern.search(name):
                                logger.info(f"Match found: '{name}'")
                                results.append(self._entry_to_dict(entry))
                                if len(results) >= limit:
                                    break
                        except Exception as e:
                            logger.error(f"Error processing entry {count}: {e}")
                            
                        if not tag_file.next(entry):
                            break
                    logger.info(f"Regex search checked {count} entries, found {len(results)} matches")
                else:
                    logger.warning("Failed to get first entry from tags file")
            else:
                # Use CTags built-in search - python-ctags3 expects bytes for symbol name
                symbol_bytes = symbol_name.encode('utf-8') if isinstance(symbol_name, str) else symbol_name
                if tag_file.find(entry, symbol_bytes, options):
                    results.append(self._entry_to_dict(entry))
                    
                    # Find additional matches
                    while len(results) < limit and tag_file.findNext(entry):
                        results.append(self._entry_to_dict(entry))
        except Exception as e:
            logger.error(f"Error searching tags: {e}")
        
        return results
    
    def get_symbols_in_file(
        self,
        tags_file: str,
        file_path: str
    ) -> List[Dict[str, Any]]:
        """Get all symbols in a specific file.
        
        Args:
            tags_file: Path to tags file
            file_path: Path to source file
            
        Returns:
            List of symbols in the file
        """
        tag_file = self.open_tags_file(tags_file)
        if not tag_file:
            return []
        
        results = []
        entry = TagEntry()
        
        # Normalize file path
        file_path = os.path.abspath(file_path)
        
        try:
            if tag_file.first(entry):
                while True:
                    entry_file = entry['file']
                    # Handle bytes from ctags
                    if isinstance(entry_file, bytes):
                        entry_file = entry_file.decode('utf-8', errors='ignore')
                    
                    # Compare paths - handle both absolute and relative
                    if entry_file:
                        # Normalize both paths for comparison
                        entry_file_abs = os.path.abspath(entry_file)
                        
                        # Check if paths match (handle case where one might be relative)
                        if (entry_file_abs == file_path or 
                            entry_file == file_path or
                            os.path.samefile(entry_file_abs, file_path) if os.path.exists(entry_file_abs) and os.path.exists(file_path) else False):
                            results.append(self._entry_to_dict(entry))
                    
                    if not tag_file.next(entry):
                        break
        except Exception as e:
            logger.error(f"Error reading tags: {e}")
        
        return results
    
    def _entry_to_dict(self, entry: TagEntry) -> Dict[str, Any]:
        """Convert TagEntry to dictionary.
        
        Args:
            entry: TagEntry object
            
        Returns:
            Dictionary representation
        """
        # Handle potential bytes returned from ctags
        def decode_if_bytes(value):
            if isinstance(value, bytes):
                return value.decode('utf-8', errors='ignore')
            return value
        
        return {
            "name": decode_if_bytes(entry['name']),
            "file": decode_if_bytes(entry['file']),
            "line": entry['lineNumber'] if entry['lineNumber'] else 0,
            "kind": decode_if_bytes(entry['kind']) if entry['kind'] else None,
            "pattern": decode_if_bytes(entry['pattern']) if entry['pattern'] else None
        }
    
    def get_tags_info(self, tags_file: str) -> Dict[str, Any]:
        """Get information about a tags file.
        
        Args:
            tags_file: Path to tags file
            
        Returns:
            Tags file information
        """
        if not os.path.exists(tags_file):
            return {"error": "Tags file not found"}
        
        tag_file = self.open_tags_file(tags_file)
        if not tag_file:
            return {"error": "Failed to open tags file"}
        
        try:
            info = {
                "file": os.path.abspath(tags_file),
                "size": os.path.getsize(tags_file),
                "format": tag_file['format'],
                "sort": tag_file['sort'],
                "author": tag_file['author'] or "Unknown",
                "name": tag_file['name'] or "Unknown",
                "url": tag_file['url'] or "",
                "version": tag_file['version'] or ""
            }
            
            # Count tags
            tag_count = 0
            entry = TagEntry()
            if tag_file.first(entry):
                tag_count = 1
                while tag_file.next(entry):
                    tag_count += 1
            
            info['tag_count'] = tag_count
            return info
        except Exception as e:
            return {"error": str(e)}