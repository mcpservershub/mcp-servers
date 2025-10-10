"""
SuperBOL COBOL Language Server Client
====================================

This module provides an LSP client for SuperBOL COBOL language server.
SuperBOL is a modern COBOL LSP server that supports various COBOL dialects.
"""

import asyncio
import json
import logging
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

from .models import (
    CompletionItem, CompletionItemKind, Hover, Language, Location, Position, Range, SymbolInformation, SymbolKind
)

logger = logging.getLogger(__name__)


class SuperBOLClient:
    """LSP client for SuperBOL COBOL language server."""

    def __init__(self, workspace_root: str, cache_dir: Optional[str] = None):
        self.workspace_root = Path(workspace_root)
        self.cache_dir = Path(cache_dir) if cache_dir else self.workspace_root / ".superbol-cache"
        self.server_process: Optional[subprocess.Popen] = None
        self.request_id = 0
        self.is_initialized = False
        self.response_handlers = {}
        self.notification_handlers = {}
        self._lock = threading.Lock()

        # Ensure cache directory exists
        self.cache_dir.mkdir(exist_ok=True, parents=True)

    def __enter__(self):
        """Context manager entry."""
        self.start_server()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_server()

    def start_server(self):
        """Start SuperBOL LSP server."""
        if self.server_process:
            logger.warning("SuperBOL server already running")
            return

        superbol_cmd = self._get_superbol_command()
        if not superbol_cmd:
            raise RuntimeError("SuperBOL not found. Please install SuperBOL or ensure it's in PATH")

        try:
            logger.info(f"Starting SuperBOL server: {' '.join(superbol_cmd)}")
            self.server_process = subprocess.Popen(
                superbol_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.workspace_root),
                bufsize=0  # Unbuffered for real-time communication
            )

            # Initialize the server
            try:
                self._initialize_server()
                logger.info("SuperBOL server started and initialized successfully")
            except Exception as e:
                logger.error(f"SuperBOL server initialization failed: {e}")
                # Clean up the process
                if self.server_process:
                    try:
                        self.server_process.terminate()
                        self.server_process.wait(timeout=5)
                    except:
                        pass
                    self.server_process = None
                raise RuntimeError(f"SuperBOL initialization failed: {e}")

        except Exception as e:
            logger.error(f"Failed to start SuperBOL server: {e}")
            raise

    def stop_server(self):
        """Stop SuperBOL LSP server."""
        if self.server_process:
            try:
                # Send shutdown request
                self._send_request("shutdown", {})
                self._send_notification("exit", {})

                # Wait for process to terminate
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("SuperBOL server did not shutdown gracefully, terminating")
                self.server_process.terminate()
            except Exception as e:
                logger.error(f"Error stopping SuperBOL server: {e}")
            finally:
                self.server_process = None
                self.is_initialized = False

    def _get_superbol_command(self) -> Optional[List[str]]:
        """Get SuperBOL server command."""
        # Try to find superbol binary
        superbol_path = shutil.which("superbol")
        if superbol_path:
            # According to SuperBOL wiki, use "superbol-free lsp" command
            return [superbol_path, "lsp"]

        # Try common installation paths
        common_paths = [
            "/usr/local/bin/superbol",
            "/usr/bin/superbol",
            str(Path.home() / ".local/bin/superbol"),
        ]

        for path in common_paths:
            if Path(path).exists():
                return [path, "lsp"]  # Use "lsp" argument as per documentation

        logger.error("SuperBOL not found in PATH or common locations")
        return None

    def _initialize_server(self):
        """Initialize SuperBOL LSP server."""
        # Send initialize request
        init_params = {
            "processId": None,
            "rootPath": str(self.workspace_root),
            "rootUri": f"file://{self.workspace_root}",
            "initializationOptions": {
                "dialect": "gnucobol",
                "copybooks": []
            },
            "capabilities": {
                "workspace": {
                    "applyEdit": True,
                    "configuration": True,
                    "didChangeConfiguration": {
                        "dynamicRegistration": True
                    }
                },
                "textDocument": {
                    "synchronization": {
                        "dynamicRegistration": True,
                        "willSave": True,
                        "didSave": True,
                        "willSaveWaitUntil": True
                    },
                    "completion": {
                        "dynamicRegistration": True,
                        "completionItem": {
                            "snippetSupport": True,
                            "documentationFormat": ["markdown", "plaintext"]
                        }
                    },
                    "hover": {
                        "dynamicRegistration": True,
                        "contentFormat": ["markdown", "plaintext"]
                    },
                    "definition": {
                        "dynamicRegistration": True
                    },
                    "references": {
                        "dynamicRegistration": True
                    },
                    "documentSymbol": {
                        "dynamicRegistration": True
                    }
                }
            },
            "trace": "off",
            "workspaceFolders": [
                {
                    "uri": f"file://{self.workspace_root}",
                    "name": self.workspace_root.name
                }
            ]
        }

        logger.debug(f"Sending initialize request with params: {init_params}")
        response = self._send_request("initialize", init_params)
        logger.debug(f"Initialize response: {response}")

        if response.get("error"):
            logger.error(f"SuperBOL initialization error: {response['error']}")
            raise RuntimeError(f"Server initialization failed: {response['error']}")

        if not response.get("result"):
            logger.error(f"SuperBOL initialization failed: no result in response")
            raise RuntimeError("Server initialization failed: no result returned")

        # Send initialized notification
        self._send_notification("initialized", {})
        self.is_initialized = True
        logger.info("SuperBOL server initialized successfully")

    def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send LSP request to SuperBOL server."""
        with self._lock:
            if not self.server_process:
                raise RuntimeError("SuperBOL server not running")

            self.request_id += 1
            request_id = self.request_id

            request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params
            }

            self._write_message(request)
            return self._read_response(request_id)

    def _send_notification(self, method: str, params: Dict[str, Any]):
        """Send LSP notification to SuperBOL server."""
        with self._lock:
            if not self.server_process:
                raise RuntimeError("SuperBOL server not running")

            notification = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params
            }

            self._write_message(notification)

    def _write_message(self, message: Dict[str, Any]):
        """Write LSP message to server stdin."""
        content = json.dumps(message)
        content_length = len(content.encode('utf-8'))

        full_message = f"Content-Length: {content_length}\r\n\r\n{content}"

        if self.server_process and self.server_process.stdin:
            self.server_process.stdin.write(full_message)
            self.server_process.stdin.flush()
            logger.debug(f"Sent: {message['method']}")

    def _read_response(self, request_id: int, timeout: float = 30.0) -> Dict[str, Any]:
        """Read LSP response from server stdout."""
        start_time = time.time()
        logger.debug(f"Starting _read_response for request {request_id}")

        while time.time() - start_time < timeout:
            try:
                if not self.server_process or not self.server_process.stdout:
                    logger.error("Server process not available")
                    raise RuntimeError("Server process not available")

                # Check if process has terminated
                poll_result = self.server_process.poll()
                logger.debug(f"Process poll result: {poll_result}")

                if poll_result is not None:
                    # Process has exited
                    return_code = self.server_process.returncode
                    stderr_output = ""
                    if self.server_process.stderr:
                        try:
                            stderr_output = self.server_process.stderr.read() or ""
                        except Exception as e:
                            logger.debug(f"Error reading stderr: {e}")
                            stderr_output = ""

                    error_msg = f"SuperBOL process exited with code {return_code}"
                    if stderr_output.strip():
                        error_msg += f": {stderr_output.strip()}"

                    logger.error(error_msg)
                    raise RuntimeError(error_msg)

                # Read Content-Length header
                header_line = self.server_process.stdout.readline()
                if not header_line:
                    time.sleep(0.1)
                    continue

                if not header_line.startswith("Content-Length:"):
                    continue

                content_length = int(header_line.split(":")[1].strip())

                # Read empty line
                self.server_process.stdout.readline()

                # Read content
                content = self.server_process.stdout.read(content_length)
                if not content:
                    continue

                message = json.loads(content)

                # Check if this is the response we're waiting for
                if "id" in message and message["id"] == request_id:
                    logger.debug(f"Received response for {request_id}")
                    return message

                # Handle notifications or other messages
                logger.debug(f"Received other message: {message.get('method', 'response')}")

            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON response: {e}")
                continue
            except Exception as e:
                logger.error(f"Error reading response: {e}")
                # Check if the process has exited due to the error
                if self.server_process and self.server_process.poll() is not None:
                    return_code = self.server_process.returncode
                    raise RuntimeError(f"SuperBOL process exited with code {return_code} during communication")
                # Otherwise continue trying (might be a temporary error)
                continue

        raise TimeoutError(f"No response received for request {request_id} within {timeout}s")

    def _file_to_uri(self, file_path: str) -> str:
        """Convert file path to URI."""
        abs_path = self.workspace_root / file_path
        return f"file://{abs_path}"

    def _uri_to_path(self, uri: str) -> str:
        """Convert URI to relative file path."""
        if uri.startswith("file://"):
            abs_path = Path(uri[7:])
            try:
                return str(abs_path.relative_to(self.workspace_root))
            except ValueError:
                return str(abs_path)
        return uri

    def _ensure_document_open(self, file_path: str):
        """Ensure document is opened in the language server."""
        abs_path = self.workspace_root / file_path
        if not abs_path.exists():
            logger.warning(f"File does not exist: {abs_path}")
            return

        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Send textDocument/didOpen notification
            self._send_notification("textDocument/didOpen", {
                "textDocument": {
                    "uri": self._file_to_uri(file_path),
                    "languageId": "cobol",
                    "version": 1,
                    "text": content
                }
            })

            # Small delay to allow server to process
            time.sleep(0.1)

        except Exception as e:
            logger.error(f"Failed to open document {file_path}: {e}")

    # LSP Method Implementations

    def get_document_symbols(self, file_path: str) -> List[SymbolInformation]:
        """Get document symbols for a COBOL file."""
        if not self.is_initialized:
            raise RuntimeError("Server not initialized")

        self._ensure_document_open(file_path)

        response = self._send_request("textDocument/documentSymbol", {
            "textDocument": {
                "uri": self._file_to_uri(file_path)
            }
        })

        if "error" in response:
            logger.error(f"Document symbols error: {response['error']}")
            return []

        symbols = response.get("result", [])
        return [self._convert_symbol(symbol) for symbol in symbols]

    def get_hover(self, file_path: str, line: int, column: int) -> Optional[Hover]:
        """Get hover information for a position."""
        if not self.is_initialized:
            raise RuntimeError("Server not initialized")

        self._ensure_document_open(file_path)

        response = self._send_request("textDocument/hover", {
            "textDocument": {
                "uri": self._file_to_uri(file_path)
            },
            "position": {
                "line": line,
                "character": column
            }
        })

        if "error" in response:
            logger.error(f"Hover error: {response['error']}")
            return None

        hover_data = response.get("result")
        if not hover_data:
            return None

        return self._convert_hover(hover_data)

    def get_definitions(self, file_path: str, line: int, column: int) -> List[Location]:
        """Get definitions for a symbol at the given position."""
        if not self.is_initialized:
            raise RuntimeError("Server not initialized")

        self._ensure_document_open(file_path)

        response = self._send_request("textDocument/definition", {
            "textDocument": {
                "uri": self._file_to_uri(file_path)
            },
            "position": {
                "line": line,
                "character": column
            }
        })

        if "error" in response:
            logger.error(f"Definition error: {response['error']}")
            return []

        locations = response.get("result", [])
        if not isinstance(locations, list):
            locations = [locations] if locations else []

        return [self._convert_location(loc) for loc in locations if loc]

    def get_references(self, file_path: str, line: int, column: int) -> List[Location]:
        """Get references for a symbol at the given position."""
        if not self.is_initialized:
            raise RuntimeError("Server not initialized")

        self._ensure_document_open(file_path)

        response = self._send_request("textDocument/references", {
            "textDocument": {
                "uri": self._file_to_uri(file_path)
            },
            "position": {
                "line": line,
                "character": column
            },
            "context": {
                "includeDeclaration": True
            }
        })

        if "error" in response:
            logger.error(f"References error: {response['error']}")
            return []

        locations = response.get("result", [])
        if locations is None:
            locations = []
        return [self._convert_location(loc) for loc in locations if loc]

    def get_completions(self, file_path: str, line: int, column: int) -> List[CompletionItem]:
        """Get code completions for a position."""
        if not self.is_initialized:
            raise RuntimeError("Server not initialized")

        self._ensure_document_open(file_path)

        response = self._send_request("textDocument/completion", {
            "textDocument": {
                "uri": self._file_to_uri(file_path)
            },
            "position": {
                "line": line,
                "character": column
            }
        })

        if "error" in response:
            logger.error(f"Completion error: {response['error']}")
            return []

        result = response.get("result", {})
        items = result.get("items", []) if isinstance(result, dict) else result or []

        return [self._convert_completion_item(item) for item in items]

    def get_workspace_symbols(self, query: str) -> List[SymbolInformation]:
        """Get workspace symbols matching a query."""
        if not self.is_initialized:
            raise RuntimeError("Server not initialized")

        response = self._send_request("workspace/symbol", {
            "query": query
        })

        if "error" in response:
            logger.error(f"Workspace symbols error: {response['error']}")
            return []

        symbols = response.get("result", [])
        return [self._convert_symbol(symbol) for symbol in symbols]

    # Conversion methods

    def _convert_symbol(self, symbol_data: Dict[str, Any]) -> SymbolInformation:
        """Convert LSP DocumentSymbol/SymbolInformation to our format."""
        name = symbol_data.get("name", "")
        kind = symbol_data.get("kind", 1)

        # Handle both DocumentSymbol and SymbolInformation formats
        if "location" in symbol_data:
            # SymbolInformation format
            location = symbol_data["location"]
            uri = location.get("uri", "")
            range_data = location.get("range", {})
        else:
            # DocumentSymbol format
            uri = ""  # Will be filled by caller
            range_data = symbol_data.get("range", {})

        return SymbolInformation(
            name=name,
            kind=SymbolKind(kind),
            location=Location(
                uri=uri,
                range=self._convert_range(range_data),
                relative_path=self._uri_to_path(uri) if uri else ""
            ),
            container_name=symbol_data.get("containerName"),
            deprecated=symbol_data.get("deprecated", False)
        )

    def _convert_location(self, location_data: Dict[str, Any]) -> Location:
        """Convert LSP Location to our format."""
        uri = location_data.get("uri", "")
        return Location(
            uri=uri,
            range=self._convert_range(location_data.get("range", {})),
            relative_path=self._uri_to_path(uri)
        )

    def _convert_range(self, range_data: Dict[str, Any]) -> Range:
        """Convert LSP Range to our format."""
        start = range_data.get("start", {})
        end = range_data.get("end", {})

        return Range(
            start=Position(
                line=start.get("line", 0),
                character=start.get("character", 0)
            ),
            end=Position(
                line=end.get("line", 0),
                character=end.get("character", 0)
            )
        )

    def _convert_hover(self, hover_data: Dict[str, Any]) -> Hover:
        """Convert LSP Hover to our format."""
        contents = hover_data.get("contents", [])

        # Handle different content formats
        if isinstance(contents, str):
            content_str = contents
        elif isinstance(contents, list):
            content_str = "\\n".join(
                item.get("value", str(item)) if isinstance(item, dict) else str(item)
                for item in contents
            )
        elif isinstance(contents, dict):
            content_str = contents.get("value", str(contents))
        else:
            content_str = str(contents)

        return Hover(
            contents=content_str,
            range=self._convert_range(hover_data.get("range", {}))
        )

    def _convert_completion_item(self, item_data: Dict[str, Any]) -> CompletionItem:
        """Convert LSP CompletionItem to our format."""
        return CompletionItem(
            label=item_data.get("label", ""),
            kind=CompletionItemKind(item_data.get("kind", 1)),
            detail=item_data.get("detail"),
            documentation=item_data.get("documentation"),
            deprecated=item_data.get("deprecated", False),
            preselect=item_data.get("preselect", False)
        )