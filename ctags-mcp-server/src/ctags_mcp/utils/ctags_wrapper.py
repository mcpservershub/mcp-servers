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

    # Custom language mappings for non-standard extensions
    CUSTOM_LANGUAGE_MAPPINGS = {
        "Cobol": [".c74", ".cob74", ".cbl74"]  # COBOL74 and other variants
    }

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

    def _get_language_mapping_options(self) -> List[str]:
        """Get custom language mapping options for ctags.

        Returns:
            List of --map-<LANG>=+.<ext> options
        """
        options = []
        for lang, extensions in self.CUSTOM_LANGUAGE_MAPPINGS.items():
            for ext in extensions:
                options.append(f"--map-{lang}=+{ext}")
        return options

    def generate_tags(
        self,
        path: str,
        output_file: str = "tags",
        recursive: bool = True,
        languages: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        output_format: str = "u-ctags",
        extra_options: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate tags file for given path.

        Args:
            path: Path to index
            output_file: Output tags file
            recursive: Recursive indexing
            languages: Languages to include
            exclude_patterns: Patterns to exclude
            output_format: Output format (u-ctags, e-ctags, etags, xref, json)
            extra_options: Extra ctags options

        Returns:
            Dictionary with generation results
        """
        cmd = [self.ctags_binary]

        # Add custom language mappings
        cmd.extend(self._get_language_mapping_options())

        # Add output file
        cmd.extend(["-f", output_file])

        # Add output format
        if output_format and output_format != "u-ctags":
            if output_format == "etags":
                cmd.append("-e")
            elif output_format == "xref":
                cmd.append("-x")
            elif output_format in ["e-ctags", "json"]:
                cmd.extend(["--output-format=" + output_format])

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

        # Add fields for better tag information (not applicable for xref format)
        if output_format != "xref":
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
                # For xref format, output goes to stdout, so we need to save it to file
                if output_format == "xref":
                    with open(output_file, 'w') as f:
                        f.write(result.stdout)

                    # Count lines in xref output (each line is an entry)
                    tag_count = len([line for line in result.stdout.strip().split('\n') if line.strip()])
                else:
                    # Count tags generated from file
                    tag_count = 0
                    if os.path.exists(output_file):
                        with open(output_file, 'r') as f:
                            tag_count = sum(1 for line in f if not line.startswith('!'))

                return {
                    "success": True,
                    "tags_file": os.path.abspath(output_file),
                    "tag_count": tag_count,
                    "command": " ".join(cmd),
                    "format": output_format
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
    
    def get_all_files_from_tags(self, tags_file: str) -> List[str]:
        """Get list of all unique files referenced in tags file.

        Args:
            tags_file: Path to tags file

        Returns:
            List of unique file paths
        """
        tag_file = self.open_tags_file(tags_file)
        if not tag_file:
            return []

        files = set()
        entry = TagEntry()

        try:
            if tag_file.first(entry):
                while True:
                    file_path = entry['file']
                    if isinstance(file_path, bytes):
                        file_path = file_path.decode('utf-8', errors='ignore')
                    if file_path:
                        files.add(file_path)

                    if not tag_file.next(entry):
                        break
        except Exception as e:
            logger.error(f"Error reading files from tags: {e}")

        return sorted(list(files))

    def get_all_symbols_from_tags(self, tags_file: str) -> List[Dict[str, Any]]:
        """Get all symbols from tags file.

        Args:
            tags_file: Path to tags file

        Returns:
            List of all symbols
        """
        tag_file = self.open_tags_file(tags_file)
        if not tag_file:
            return []

        symbols = []
        entry = TagEntry()

        try:
            if tag_file.first(entry):
                while True:
                    symbols.append(self._entry_to_dict(entry))

                    if not tag_file.next(entry):
                        break
        except Exception as e:
            logger.error(f"Error reading symbols from tags: {e}")

        return symbols

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

    def generate_cross_reference(
        self,
        path: str,
        recursive: bool = False,
        languages: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Generate cross-reference output for a file or directory.

        Args:
            path: Path to file or directory to generate xref for
            recursive: Recursively process directories (default: False)
            languages: Languages to filter
            exclude_patterns: Patterns to exclude from indexing

        Returns:
            List of cross-reference entries
        """
        cmd = [self.ctags_binary, "-x"]

        # Add custom language mappings
        cmd.extend(self._get_language_mapping_options())

        # Add recursive flag if processing directory
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

        cmd.append(path)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                # Parse xref output
                entries = []
                is_single_file = os.path.isfile(path)

                for line in result.stdout.strip().split('\n'):
                    if line:
                        # xref format depends on single vs multi-file:
                        # Single file: name kind line pattern
                        # Multi-file: name kind line file pattern
                        parts = line.split(maxsplit=4)

                        if is_single_file and len(parts) >= 3:
                            # Single file format
                            entries.append({
                                "name": parts[0],
                                "kind": parts[1],
                                "line": int(parts[2]) if parts[2].isdigit() else 0,
                                "file": path,
                                "pattern": parts[3] if len(parts) > 3 else ""
                            })
                        elif not is_single_file and len(parts) >= 4:
                            # Multi-file format
                            entries.append({
                                "name": parts[0],
                                "kind": parts[1],
                                "line": int(parts[2]) if parts[2].isdigit() else 0,
                                "file": parts[3],
                                "pattern": parts[4] if len(parts) > 4 else ""
                            })
                return entries
            else:
                logger.error(f"Cross-reference generation failed: {result.stderr}")
                return []
        except Exception as e:
            logger.error(f"Error generating cross-reference: {e}")
            return []

    def detect_language(self, file_path: str) -> Optional[str]:
        """Detect the language of a file.

        Args:
            file_path: Path to file

        Returns:
            Detected language name or None
        """
        cmd = [self.ctags_binary]

        # Add custom language mappings
        cmd.extend(self._get_language_mapping_options())

        cmd.extend(["--print-language", file_path])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            return None

    def list_languages(self) -> List[str]:
        """List all supported languages.

        Returns:
            List of language names
        """
        cmd = [self.ctags_binary, "--list-languages"]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return [lang.strip() for lang in result.stdout.strip().split('\n') if lang.strip()]
            return []
        except Exception as e:
            logger.error(f"Error listing languages: {e}")
            return []

    def list_tag_kinds(self, language: str) -> Dict[str, Any]:
        """List tag kinds for a specific language.

        Args:
            language: Language name

        Returns:
            Dictionary with kind information
        """
        cmd = [self.ctags_binary, "--list-kinds-full=" + language]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                kinds = {}
                lines = result.stdout.strip().split('\n')

                # Skip header line if present
                start_idx = 1 if lines and ('LETTER' in lines[0] or 'NAME' in lines[0]) else 0

                for line in lines[start_idx:]:
                    if line.strip():
                        # Format: LETTER NAME ENABLED REFONLY NROLES MASTER DESCRIPTION
                        parts = line.split(maxsplit=6)
                        if len(parts) >= 3:
                            letter = parts[0]
                            name = parts[1]
                            enabled = parts[2] == 'yes' if len(parts) > 2 else True
                            description = parts[6] if len(parts) > 6 else ""

                            kinds[letter] = {
                                "name": name,
                                "enabled": enabled,
                                "description": description
                            }
                return {
                    "language": language,
                    "kinds": kinds
                }
            else:
                return {"error": f"Language '{language}' not found or not supported"}
        except Exception as e:
            logger.error(f"Error listing tag kinds: {e}")
            return {"error": str(e)}