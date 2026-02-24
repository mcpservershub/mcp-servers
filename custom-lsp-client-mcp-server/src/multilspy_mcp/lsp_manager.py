"""
LSP Manager - Wrapper around MultilsPy for managing Language Server instances.
"""

import os
import json
import asyncio
import logging
import re
from pathlib import Path
from typing import Dict, Optional, List, Any, Union
from datetime import datetime
from contextlib import asynccontextmanager, contextmanager

from multilspy import LanguageServer, SyncLanguageServer
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger
from multilspy import multilspy_types

from .models import (
    Language, Location, Position, Range, CompletionItem,
    SymbolInformation, Hover, WorkspaceConfig, SessionState
)
from .superbol_client import SuperBOLClient


class LSPManager:
    """
    Manager class for handling MultilsPy Language Server instances.
    Provides caching, state management, and enhanced functionality.
    """
    
    def __init__(self, workspace_root: str, cache_dir: Optional[str] = None):
        """
        Initialize the LSP Manager.
        
        Args:
            workspace_root: Root directory of the workspace
            cache_dir: Directory for caching and state persistence
        """
        self.workspace_root = Path(workspace_root).resolve()
        self.cache_dir = Path(cache_dir or "~/.mcp-lsp/cache").expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Language server instances cache
        self._lsp_instances: Dict[Language, SyncLanguageServer] = {}
        self._async_instances: Dict[Language, LanguageServer] = {}
        
        # Session management
        self.session_id = datetime.now().isoformat()
        self.session_file = self.cache_dir / f"session_{self.session_id}.json"
        
        # Logger
        self.logger = self._setup_logger()
        
        # File buffers and state
        self.open_files: Dict[str, Dict[str, Any]] = {}
        self.capabilities: Dict[Language, Dict[str, Any]] = {}
        self.symbol_cache: Dict[str, List[SymbolInformation]] = {}

        # SuperBOL client for COBOL support
        self.superbol_client: Optional[SuperBOLClient] = None
        
    def _setup_logger(self) -> MultilspyLogger:
        """Setup MultilsPy logger."""
        logger = MultilspyLogger()
        # MultilspyLogger doesn't have set_level, it uses its own logging mechanism
        return logger
    
    def detect_language(self, file_path: str) -> Optional[Language]:
        """
        Detect language from file extension and workspace context.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected language or None
        """
        file_ext = Path(file_path).suffix.lower()
        
        # Extension to language mapping
        ext_map = {
            '.py': Language.PYTHON,
            '.java': Language.JAVA,
            '.rs': Language.RUST,
            '.cs': Language.CSHARP,
            '.ts': Language.TYPESCRIPT,
            '.tsx': Language.TYPESCRIPT,
            '.js': Language.JAVASCRIPT,
            '.jsx': Language.JAVASCRIPT,
            '.go': Language.GO,
            '.rb': Language.RUBY,
            '.dart': Language.DART,
            '.kt': Language.KOTLIN,
            '.cpp': Language.CPP,
            '.cc': Language.CPP,
            '.cxx': Language.CPP,
            '.c++': Language.CPP,
            '.h': Language.CPP,
            '.hpp': Language.CPP,
            # COBOL extensions
            '.cbl': Language.COBOL,
            '.cob': Language.COBOL,
            '.cobol': Language.COBOL,
            '.cpy': Language.COBOL,  # COBOL copybook
            '.pco': Language.COBOL,  # Pro*COBOL
            '.c74': Language.COBOL,  # COBOL 74
        }
        
        return ext_map.get(file_ext)
    
    def _get_multilspy_language(self, language: Language) -> str:
        """Convert our Language enum to MultilsPy language string."""
        # MultilsPy uses slightly different naming
        mapping = {
            Language.CSHARP: "csharp",
            Language.CPP: "cpp",
        }
        return mapping.get(language, language.value)

    def get_superbol_client(self) -> SuperBOLClient:
        """Get or create SuperBOL client for COBOL support."""
        if not self.superbol_client:
            self.superbol_client = SuperBOLClient(
                workspace_root=str(self.workspace_root),
                cache_dir=str(self.cache_dir / "superbol")
            )
        return self.superbol_client

    def is_cobol_language(self, language: Optional[Language]) -> bool:
        """Check if the language is COBOL."""
        return language == Language.COBOL
    
    def get_sync_server(self, language: Language, timeout: int = 30) -> SyncLanguageServer:
        """
        Get or create a synchronous language server instance.
        
        Args:
            language: Programming language
            timeout: Request timeout in seconds
            
        Returns:
            SyncLanguageServer instance
        """
        if language not in self._lsp_instances:
            config = MultilspyConfig.from_dict({
                "code_language": self._get_multilspy_language(language),
                "trace_lsp_communication": False,
                "start_independent_lsp_process": True
            })
            
            self._lsp_instances[language] = SyncLanguageServer.create(
                config,
                self.logger,
                str(self.workspace_root),
                timeout=timeout
            )
            
            # Store capabilities after initialization
            self.capabilities[language] = {}
            
        return self._lsp_instances[language]
    
    async def get_async_server(self, language: Language) -> LanguageServer:
        """
        Get or create an asynchronous language server instance.
        
        Args:
            language: Programming language
            
        Returns:
            LanguageServer instance
        """
        if language not in self._async_instances:
            config = MultilspyConfig.from_dict({
                "code_language": self._get_multilspy_language(language),
                "trace_lsp_communication": False,
                "start_independent_lsp_process": True
            })
            
            self._async_instances[language] = LanguageServer.create(
                config,
                self.logger,
                str(self.workspace_root)
            )
            
            # Store capabilities after initialization
            self.capabilities[language] = {}
            
        return self._async_instances[language]
    
    @contextmanager
    def start_sync_server(self, language: Language):
        """
        Context manager for starting a synchronous language server.
        
        Args:
            language: Programming language
            
        Yields:
            Started SyncLanguageServer instance
        """
        server = self.get_sync_server(language)
        with server.start_server():
            yield server
    
    @asynccontextmanager
    async def start_async_server(self, language: Language):
        """
        Context manager for starting an asynchronous language server.
        
        Args:
            language: Programming language
            
        Yields:
            Started LanguageServer instance
        """
        server = await self.get_async_server(language)
        async with server.start_server():
            yield server
    
    def _convert_location(self, loc: dict) -> Location:
        """Convert MultilsPy location to our Location model."""
        return Location(
            uri=loc.get("uri", ""),
            range=Range(
                start=Position(
                    line=loc["range"]["start"]["line"],
                    character=loc["range"]["start"]["character"]
                ),
                end=Position(
                    line=loc["range"]["end"]["line"],
                    character=loc["range"]["end"]["character"]
                )
            ),
            absolute_path=loc.get("absolutePath"),
            relative_path=loc.get("relativePath")
        )
    
    def _convert_completion(self, item: dict) -> CompletionItem:
        """Convert MultilsPy completion item to our CompletionItem model."""
        return CompletionItem(
            completion_text=item.get("completionText", item.get("label", "")),
            kind=item.get("kind", 1),
            detail=item.get("detail"),
            documentation=item.get("documentation"),
            sort_text=item.get("sortText"),
            filter_text=item.get("filterText"),
            insert_text=item.get("insertText"),
            label=item.get("label")
        )
    
    def _convert_symbol(self, sym: dict) -> SymbolInformation:
        """Convert MultilsPy symbol to our SymbolInformation model."""
        location = None
        if "location" in sym:
            location = self._convert_location(sym["location"])
            
        range_data = None
        if "range" in sym:
            range_data = Range(
                start=Position(
                    line=sym["range"]["start"]["line"],
                    character=sym["range"]["start"]["character"]
                ),
                end=Position(
                    line=sym["range"]["end"]["line"],
                    character=sym["range"]["end"]["character"]
                )
            )
            
        return SymbolInformation(
            name=sym.get("name", ""),
            kind=sym.get("kind", 1),
            location=location,
            container_name=sym.get("containerName"),
            deprecated=sym.get("deprecated", False),
            detail=sym.get("detail"),
            range=range_data,
            selection_range=range_data,
            children=[]
        )
    
    def _convert_hover(self, hover: dict) -> Hover:
        """Convert MultilsPy hover to our Hover model."""
        contents = hover.get("contents", "")
        
        # Handle different content formats
        if isinstance(contents, dict):
            if "value" in contents:
                contents = contents["value"]
            elif "kind" in contents and "value" in contents:
                contents = f"```{contents['kind']}\n{contents['value']}\n```"
                
        range_data = None
        if "range" in hover:
            range_data = Range(
                start=Position(
                    line=hover["range"]["start"]["line"],
                    character=hover["range"]["start"]["character"]
                ),
                end=Position(
                    line=hover["range"]["end"]["line"],
                    character=hover["range"]["end"]["character"]
                )
            )
            
        return Hover(contents=contents, range=range_data)
    
    def request_definition(
        self,
        file_path: str,
        line: int,
        column: int,
        language: Optional[Language] = None
    ) -> List[Location]:
        """
        Request definition locations for a symbol.
        
        Args:
            file_path: Relative file path
            line: Line number (0-indexed)
            column: Column number (0-indexed)
            language: Optional language hint
            
        Returns:
            List of definition locations
        """
        lang = language or self.detect_language(file_path)
        if not lang:
            raise ValueError(f"Cannot detect language for {file_path}")

        # Handle COBOL with SuperBOL
        if self.is_cobol_language(lang):
            client = self.get_superbol_client()
            with client:
                return client.get_definitions(file_path, line, column)

        # Convert to absolute path for MultilsPy
        abs_path = str(self.workspace_root / file_path)

        with self.start_sync_server(lang) as server:
            results = server.request_definition(abs_path, line, column)
            return [self._convert_location(loc) for loc in results]
    
    def request_references(
        self,
        file_path: str,
        line: int,
        column: int,
        language: Optional[Language] = None
    ) -> List[Location]:
        """
        Request references for a symbol.
        
        Args:
            file_path: Relative file path
            line: Line number (0-indexed)
            column: Column number (0-indexed)
            language: Optional language hint
            
        Returns:
            List of reference locations
        """
        lang = language or self.detect_language(file_path)
        if not lang:
            raise ValueError(f"Cannot detect language for {file_path}")

        # Handle COBOL with SuperBOL
        if self.is_cobol_language(lang):
            client = self.get_superbol_client()
            with client:
                return client.get_references(file_path, line, column)

        # Convert to absolute path for MultilsPy
        abs_path = str(self.workspace_root / file_path)

        with self.start_sync_server(lang) as server:
            results = server.request_references(abs_path, line, column)
            return [self._convert_location(loc) for loc in results]
    
    def request_completions(
        self,
        file_path: str,
        line: int,
        column: int,
        language: Optional[Language] = None,
        allow_incomplete: bool = False
    ) -> List[CompletionItem]:
        """
        Request code completions.
        
        Args:
            file_path: Relative file path
            line: Line number (0-indexed)
            column: Column number (0-indexed)
            language: Optional language hint
            allow_incomplete: Allow incomplete results
            
        Returns:
            List of completion items
        """
        lang = language or self.detect_language(file_path)
        if not lang:
            raise ValueError(f"Cannot detect language for {file_path}")

        # Handle COBOL with SuperBOL
        if self.is_cobol_language(lang):
            client = self.get_superbol_client()
            with client:
                return client.get_completions(file_path, line, column)

        # Convert to absolute path for MultilsPy
        abs_path = str(self.workspace_root / file_path)

        with self.start_sync_server(lang) as server:
            results = server.request_completions(abs_path, line, column, allow_incomplete)
            return [self._convert_completion(item) for item in results]
    
    def request_document_symbols(
        self,
        file_path: str,
        language: Optional[Language] = None
    ) -> List[SymbolInformation]:
        """
        Request document symbols.
        
        Args:
            file_path: Relative file path
            language: Optional language hint
            
        Returns:
            List of document symbols
        """
        lang = language or self.detect_language(file_path)
        if not lang:
            raise ValueError(f"Cannot detect language for {file_path}")
        
        # Check cache first
        cache_key = f"{lang.value}:{file_path}"
        if cache_key in self.symbol_cache:
            return self.symbol_cache[cache_key]

        # Handle COBOL with SuperBOL
        if self.is_cobol_language(lang):
            client = self.get_superbol_client()
            with client:
                result = client.get_document_symbols(file_path)
                # Cache the results
                self.symbol_cache[cache_key] = result
                return result

        # Convert to absolute path for MultilsPy
        abs_path = str(self.workspace_root / file_path)

        with self.start_sync_server(lang) as server:
            symbols, _ = server.request_document_symbols(abs_path)
            result = [self._convert_symbol(sym) for sym in symbols]

            # Cache the results
            self.symbol_cache[cache_key] = result
            return result
    
    def request_hover(
        self,
        file_path: str,
        line: int,
        column: int,
        language: Optional[Language] = None
    ) -> Optional[Hover]:
        """
        Request hover information.
        
        Args:
            file_path: Relative file path
            line: Line number (0-indexed)
            column: Column number (0-indexed)
            language: Optional language hint
            
        Returns:
            Hover information or None
        """
        lang = language or self.detect_language(file_path)
        if not lang:
            raise ValueError(f"Cannot detect language for {file_path}")

        # Handle COBOL with SuperBOL
        if self.is_cobol_language(lang):
            client = self.get_superbol_client()
            with client:
                return client.get_hover(file_path, line, column)

        # Convert to absolute path for MultilsPy
        abs_path = str(self.workspace_root / file_path)

        with self.start_sync_server(lang) as server:
            result = server.request_hover(abs_path, line, column)
            return self._convert_hover(result) if result else None
    
    def request_workspace_symbol(
        self,
        query: str,
        language: Optional[Language] = None
    ) -> List[SymbolInformation]:
        """
        Request workspace symbols.
        
        Args:
            query: Search query
            language: Optional language hint
            
        Returns:
            List of matching symbols
        """
        # If language is specified, search in that language
        if language:
            # Handle COBOL with SuperBOL
            if self.is_cobol_language(language):
                client = self.get_superbol_client()
                with client:
                    return client.get_workspace_symbols(query)

            with self.start_sync_server(language) as server:
                results = server.request_workspace_symbol(query)
                return [self._convert_symbol(sym) for sym in (results or [])]

        # Otherwise, search across all initialized languages
        all_symbols = []

        # Search COBOL with SuperBOL if available
        if self.superbol_client:
            try:
                with self.get_superbol_client() as client:
                    cobol_symbols = client.get_workspace_symbols(query)
                    all_symbols.extend(cobol_symbols)
            except Exception as e:
                logging.error(f"Error searching COBOL symbols: {e}")

        for lang in self._lsp_instances:
            with self.start_sync_server(lang) as server:
                results = server.request_workspace_symbol(query)
                if results:
                    all_symbols.extend([self._convert_symbol(sym) for sym in results])

        return all_symbols
    
    def save_session(self) -> None:
        """Save current session state to disk."""
        state = SessionState(
            session_id=self.session_id,
            workspace_config=WorkspaceConfig(
                root_path=str(self.workspace_root),
                language=Language.PYTHON  # Default, should be detected
            ),
            open_files=list(self.open_files.keys()),
            capabilities=self.capabilities,
            diagnostics_cache={},
            symbol_cache={k: [s.model_dump() for s in v] for k, v in self.symbol_cache.items()},
            created_at=self.session_id,
            updated_at=datetime.now().isoformat()
        )
        
        with open(self.session_file, 'w') as f:
            json.dump(state.model_dump(), f, indent=2)
    
    def load_session(self, session_file: str) -> None:
        """Load session state from disk."""
        with open(session_file, 'r') as f:
            data = json.load(f)
            state = SessionState(**data)
            
            self.session_id = state.session_id
            self.workspace_root = Path(state.workspace_config.root_path)
            self.capabilities = state.capabilities or {}
            
            # Restore symbol cache
            for key, symbols in (state.symbol_cache or {}).items():
                self.symbol_cache[key] = [SymbolInformation(**sym) for sym in symbols]
    
    def generate_cobol_cfg(
        self,
        file_path: str,
        section_name: Optional[str] = None,
        output_format: str = "dot",
        collapse_fallthrough: bool = False
    ) -> Dict[str, Any]:
        """
        Generate Control-Flow Graph for a COBOL file.

        Args:
            file_path: Path to COBOL file
            section_name: Specific section/paragraph to analyze (optional)
            output_format: Output format ('dot', 'json', 'arc')
            collapse_fallthrough: Collapse sequential fallthrough statements

        Returns:
            CFG data in requested format
        """
        # Get document symbols to understand program structure
        symbols = self.request_document_symbols(file_path, Language.COBOL)

        # Read the COBOL file for analysis
        abs_path = self.workspace_root / file_path
        with open(abs_path, 'r') as f:
            content = f.read()
            lines = content.splitlines()

        # Parse COBOL control flow
        cfg_data = self._parse_cobol_control_flow(
            lines, symbols, section_name, collapse_fallthrough
        )

        # Format output based on requested format
        if output_format == "dot":
            return self._format_cfg_as_dot(cfg_data)
        elif output_format == "json":
            return cfg_data
        elif output_format == "arc":
            return self._format_cfg_as_arc(cfg_data)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def generate_cobol_project_cfg(
        self,
        file_pattern: Optional[str] = None,
        output_format: str = "dot",
        include_calls: bool = True,
        collapse_fallthrough: bool = False
    ) -> Dict[str, Any]:
        """
        Generate Control-Flow Graphs for all COBOL files in project.

        Args:
            file_pattern: Glob pattern to filter files
            output_format: Output format ('dot', 'json', 'arc')
            include_calls: Include inter-program CALL relationships
            collapse_fallthrough: Collapse sequential fallthrough statements

        Returns:
            Project-wide CFG data
        """
        import glob

        # Default COBOL file patterns
        if not file_pattern:
            patterns = ["**/*.cob", "**/*.COB", "**/*.cbl", "**/*.CBL", "**/*.cpy", "**/*.CPY", "**/*.c74", "**/*.C74"]
        else:
            patterns = [file_pattern]

        # Find all COBOL files
        cobol_files = []
        for pattern in patterns:
            matches = glob.glob(str(self.workspace_root / pattern), recursive=True)
            cobol_files.extend([
                str(Path(f).relative_to(self.workspace_root)) for f in matches
            ])

        # Remove duplicates
        cobol_files = list(set(cobol_files))

        # Generate CFG for each file
        project_cfg = {
            "workspace_root": str(self.workspace_root),
            "file_pattern": file_pattern,
            "files": []
        }

        call_graph = {} if include_calls else None

        for file_path in cobol_files:
            try:
                cfg = self.generate_cobol_cfg(
                    file_path,
                    output_format=output_format,
                    collapse_fallthrough=collapse_fallthrough
                )

                project_cfg["files"].append({
                    "file_path": file_path,
                    "cfg": cfg
                })

                # Extract CALL relationships if requested
                if include_calls:
                    # Get calls from raw_cfg if using formatted output
                    raw_cfg = cfg.get("raw_cfg", cfg)
                    if "calls" in raw_cfg:
                        call_graph[file_path] = raw_cfg.get("calls", [])

            except Exception as e:
                self.logger.log(f"Error generating CFG for {file_path}: {e}", logging.WARNING)

        # Add call graph if generated
        if call_graph:
            project_cfg["call_graph"] = call_graph

        return project_cfg

    def generate_combined_cfg_dot(self, project_cfg: Dict[str, Any]) -> str:
        """
        Generate a combined DOT file showing all programs and their call relationships.

        Args:
            project_cfg: Project CFG data from generate_cobol_project_cfg()

        Returns:
            DOT format string for the combined CFG
        """
        dot_lines = [
            "digraph COBOL_Project_CFG {",
            "  rankdir=TB;",
            "  node [shape=box, style=rounded];",
            "  compound=true;",
            ""
        ]

        # Create a subgraph for each COBOL program
        for file_data in project_cfg.get("files", []):
            file_path = file_data["file_path"]
            cfg = file_data["cfg"]

            # Extract program name from file path
            program_name = Path(file_path).stem.replace("-", "_")

            # Create subgraph cluster for this program
            dot_lines.append(f"  subgraph cluster_{program_name} {{")
            dot_lines.append(f'    label="{file_path}";')
            dot_lines.append("    style=filled;")
            dot_lines.append("    color=lightgrey;")
            dot_lines.append("")

            # Get raw CFG data
            raw_cfg = cfg.get("raw_cfg", cfg)

            # Add nodes within this program
            for node in raw_cfg.get("nodes", []):
                node_id = f"{program_name}_{node['name'].replace('-', '_')}"
                label = f"{node['name']} (L{node['line']})"
                shape = "rectangle" if node["type"] == "section" else "ellipse"
                dot_lines.append(f'    {node_id} [label="{label}", shape={shape}];')

            # Add internal edges (PERFORM, GO TO)
            for edge in raw_cfg.get("edges", []):
                from_id = f"{program_name}_{edge['from'].replace('-', '_')}"
                to_id = f"{program_name}_{edge['to'].replace('-', '_')}"
                style = "dashed" if edge["type"] == "perform" else "solid"
                dot_lines.append(f'    {from_id} -> {to_id} [style={style}, label="{edge["type"]}"];')

            dot_lines.append("  }")
            dot_lines.append("")

        # Add inter-program CALL edges
        call_graph = project_cfg.get("call_graph", {})
        if call_graph:
            dot_lines.append("  // Inter-program CALL relationships")

            # Map of called program names to file paths
            program_map = {Path(f["file_path"]).stem: f["file_path"]
                          for f in project_cfg.get("files", [])}

            for file_path, calls in call_graph.items():
                caller_program = Path(file_path).stem.replace("-", "_")

                for call in calls:
                    called_program = call["to"].replace("-", "_")
                    from_node = f"{caller_program}_{call['from'].replace('-', '_')}"

                    # Check if called program exists in project
                    if called_program.replace("_", "-") in program_map:
                        # Find entry point of called program (first node)
                        called_file = program_map[called_program.replace("_", "-")]
                        called_file_data = next((f for f in project_cfg.get("files", [])
                                                if f["file_path"] == called_file), None)

                        if called_file_data:
                            called_cfg = called_file_data["cfg"].get("raw_cfg", called_file_data["cfg"])
                            nodes = called_cfg.get("nodes", [])
                            if nodes:
                                entry_node = nodes[0]["name"].replace("-", "_")
                                to_node = f"{called_program}_{entry_node}"
                                dot_lines.append(f'  {from_node} -> {to_node} [style=bold, color=red, label="CALL"];')
                    else:
                        # External program not in project
                        external_node = f"external_{called_program}"
                        dot_lines.append(f'  {external_node} [label="{call["to"]}\\n(External)", shape=hexagon, style=filled, fillcolor=yellow];')
                        dot_lines.append(f'  {from_node} -> {external_node} [style=bold, color=red, label="CALL"];')

        # Add copybook relationships
        dot_lines.append("")
        dot_lines.append("  // Copybook inclusions (compile-time dependencies)")
        copybooks_used = set()
        for file_data in project_cfg.get("files", []):
            file_path = file_data["file_path"]
            cfg = file_data["cfg"]
            raw_cfg = cfg.get("raw_cfg", cfg)
            program_name = Path(file_path).stem.replace("-", "_")

            for copybook in raw_cfg.get("copybooks", []):
                copybook_name = copybook["name"]
                copybooks_used.add(copybook_name)

                # Create copybook node (diamond shape, cyan)
                copybook_node = f"copybook_{copybook_name.replace('-', '_')}"
                dot_lines.append(f'  {copybook_node} [label="{copybook_name}\\n(Copybook)", shape=diamond, style=filled, fillcolor=cyan];')

                # Link program to copybook
                program_node = f"{program_name}_{list(raw_cfg.get('nodes', [{}]))[0]['name'].replace('-', '_')}" if raw_cfg.get("nodes") else program_name
                dot_lines.append(f'  {program_node} -> {copybook_node} [style=dotted, color=blue, label="COPY"];')

        # Add dynamic call relationships
        dot_lines.append("")
        dot_lines.append("  // Dynamic CALL statements (runtime determined)")
        for file_data in project_cfg.get("files", []):
            file_path = file_data["file_path"]
            cfg = file_data["cfg"]
            raw_cfg = cfg.get("raw_cfg", cfg)
            program_name = Path(file_path).stem.replace("-", "_")

            for dyn_call in raw_cfg.get("dynamic_calls", []):
                # Skip if from is None
                if not dyn_call.get("from"):
                    continue

                variable_name = dyn_call["variable"]
                from_node = f"{program_name}_{dyn_call['from'].replace('-', '_')}"

                # Create dynamic call node (octagon, orange)
                dyn_node = f"dynamic_{program_name}_{variable_name.replace('-', '_')}"
                dot_lines.append(f'  {dyn_node} [label="Dynamic CALL\\n{variable_name}", shape=octagon, style=filled, fillcolor=orange];')
                dot_lines.append(f'  {from_node} -> {dyn_node} [style=dashed, color=darkorange, label="CALL"];')

        # Add entry point markers
        dot_lines.append("")
        dot_lines.append("  // Alternative entry points")
        for file_data in project_cfg.get("files", []):
            file_path = file_data["file_path"]
            cfg = file_data["cfg"]
            raw_cfg = cfg.get("raw_cfg", cfg)
            program_name = Path(file_path).stem.replace("-", "_")

            for entry in raw_cfg.get("entry_points", []):
                # Skip if context is None
                if not entry.get("context"):
                    continue

                entry_name = entry["name"]
                context_node = f"{program_name}_{entry['context'].replace('-', '_')}"

                # Create entry point node (invhouse/trapezoid, lightgreen)
                entry_node = f"entry_{program_name}_{entry_name.replace('-', '_')}"
                dot_lines.append(f'  {entry_node} [label="ENTRY\\n{entry_name}", shape=invhouse, style=filled, fillcolor=lightgreen];')
                dot_lines.append(f'  {entry_node} -> {context_node} [style=solid, color=green, label="entry"];')

        # Add external data sharing
        dot_lines.append("")
        dot_lines.append("  // External data sharing (shared memory)")
        external_data_map = {}
        for file_data in project_cfg.get("files", []):
            file_path = file_data["file_path"]
            cfg = file_data["cfg"]
            raw_cfg = cfg.get("raw_cfg", cfg)
            program_name = Path(file_path).stem.replace("-", "_")

            for ext_data in raw_cfg.get("external_data", []):
                data_name = ext_data["name"]

                # Track which programs use which external data
                if data_name not in external_data_map:
                    external_data_map[data_name] = []
                external_data_map[data_name].append(program_name)

        # Create nodes and edges for shared external data
        for data_name, programs in external_data_map.items():
            if len(programs) > 1:  # Only show if actually shared
                data_node = f"external_data_{data_name.replace('-', '_')}"
                dot_lines.append(f'  {data_node} [label="EXTERNAL\\n{data_name}", shape=cylinder, style=filled, fillcolor=lightblue];')

                # Link all programs that use this data
                for program_name in programs:
                    program_node = f"{program_name}_{'_'.join(program_name.split('_')[:2])}"  # Approximate first node
                    dot_lines.append(f'  {data_node} -> {program_node} [style=dotted, color=purple, dir=both, label="shared"];')

        # Add file sharing relationships
        dot_lines.append("")
        dot_lines.append("  // File sharing (I/O dependencies)")
        file_sharing_map = {}
        for file_data in project_cfg.get("files", []):
            file_path = file_data["file_path"]
            cfg = file_data["cfg"]
            raw_cfg = cfg.get("raw_cfg", cfg)
            program_name = Path(file_path).stem.replace("-", "_")

            for file_select in raw_cfg.get("file_sharing", []):
                physical_file = file_select.get("physical_file") or file_select["logical_name"]

                # Track which programs access which files
                if physical_file not in file_sharing_map:
                    file_sharing_map[physical_file] = []
                file_sharing_map[physical_file].append({
                    "program": program_name,
                    "logical": file_select["logical_name"]
                })

        # Create nodes and edges for shared files
        for physical_file, accessors in file_sharing_map.items():
            if len(accessors) > 1:  # Only show if file is shared
                file_node = f"file_{physical_file.replace('-', '_').replace('.', '_')}"
                dot_lines.append(f'  {file_node} [label="FILE\\n{physical_file}", shape=note, style=filled, fillcolor=lightyellow];')

                # Link all programs that access this file
                for accessor in accessors:
                    program_name = accessor["program"]
                    program_node = f"{program_name}_{'_'.join(program_name.split('_')[:2])}"  # Approximate first node
                    dot_lines.append(f'  {program_node} -> {file_node} [style=dotted, color=brown, dir=both, label="I/O"];')

        dot_lines.append("}")

        return "\n".join(dot_lines)

    def _parse_cobol_control_flow(
        self,
        lines: List[str],
        symbols: List[SymbolInformation],
        section_name: Optional[str],
        collapse_fallthrough: bool
    ) -> Dict[str, Any]:
        """Parse COBOL source to extract control flow information."""
        cfg = {
            "nodes": [],
            "edges": [],
            "calls": [],
            "performs": [],
            "gotos": [],
            "copybooks": [],        # COPY statements - compile-time includes
            "dynamic_calls": [],    # CALL with variables - runtime determined
            "entry_points": [],     # ENTRY statements - alternative entry points
            "external_data": [],    # EXTERNAL data items - shared memory
            "file_sharing": []      # SELECT statements - shared file access
        }

        current_section = None
        current_paragraph = None

        for i, line in enumerate(lines):
            line_upper = line.upper().strip()

            # Detect PROCEDURE DIVISION sections/paragraphs
            if "SECTION" in line_upper and "." in line_upper:
                current_section = line_upper.split()[0]
                cfg["nodes"].append({
                    "type": "section",
                    "name": current_section,
                    "line": i
                })
            elif line_upper and not line_upper.startswith(("*", "/")):
                # Paragraph (standalone line ending with .)
                if line_upper.endswith(".") and len(line_upper.split()) == 1:
                    current_paragraph = line_upper.replace(".", "")
                    cfg["nodes"].append({
                        "type": "paragraph",
                        "name": current_paragraph,
                        "line": i
                    })

            # Detect CALL statements (both static and dynamic)
            if "CALL" in line_upper:
                # Static CALL with literal string
                match = re.search(r'CALL\s+["\']([^"\']+)["\']', line_upper)
                if match:
                    called_program = match.group(1)
                    cfg["calls"].append({
                        "from": current_paragraph or current_section,
                        "to": called_program,
                        "line": i
                    })
                else:
                    # Dynamic CALL with variable
                    match = re.search(r'CALL\s+([A-Z0-9\-]+)', line_upper)
                    if match and not match.group(1).startswith('"'):
                        variable_name = match.group(1)
                        cfg["dynamic_calls"].append({
                            "from": current_paragraph or current_section,
                            "variable": variable_name,
                            "line": i
                        })

            # Detect PERFORM statements
            if "PERFORM" in line_upper:
                match = re.search(r'PERFORM\s+([A-Z0-9\-]+)', line_upper)
                if match:
                    target = match.group(1)
                    cfg["performs"].append({
                        "from": current_paragraph or current_section,
                        "to": target,
                        "line": i
                    })
                    cfg["edges"].append({
                        "from": current_paragraph or current_section,
                        "to": target,
                        "type": "perform"
                    })

            # Detect GO TO statements
            if "GO TO" in line_upper or "GOTO" in line_upper:
                match = re.search(r'GO\s*TO\s+([A-Z0-9\-]+)', line_upper)
                if match:
                    target = match.group(1)
                    cfg["gotos"].append({
                        "from": current_paragraph or current_section,
                        "to": target,
                        "line": i
                    })
                    cfg["edges"].append({
                        "from": current_paragraph or current_section,
                        "to": target,
                        "type": "goto"
                    })

            # Detect COPY statements (copybooks)
            if "COPY" in line_upper and not line_upper.startswith("*"):
                # COPY COPYBOOK-NAME [IN/OF LIBRARY]
                match = re.search(r'COPY\s+([A-Z0-9\-]+)', line_upper)
                if match:
                    copybook_name = match.group(1)
                    # Extract library if present
                    lib_match = re.search(r'(?:IN|OF)\s+([A-Z0-9\-]+)', line_upper)
                    library = lib_match.group(1) if lib_match else None

                    cfg["copybooks"].append({
                        "name": copybook_name,
                        "library": library,
                        "line": i,
                        "context": current_section or "DATA-DIVISION"
                    })

            # Detect ENTRY statements (alternative entry points)
            if "ENTRY" in line_upper and not line_upper.startswith("*"):
                match = re.search(r'ENTRY\s+["\']([^"\']+)["\']', line_upper)
                if match:
                    entry_name = match.group(1)
                    cfg["entry_points"].append({
                        "name": entry_name,
                        "line": i,
                        "context": current_paragraph or current_section
                    })

            # Detect EXTERNAL data items
            if "EXTERNAL" in line_upper and not line_upper.startswith("*"):
                # Look for data item name (typically 01 level or variable declaration)
                data_match = re.search(r'(\d{2})\s+([A-Z0-9\-]+).*EXTERNAL', line_upper)
                if data_match:
                    level = data_match.group(1)
                    data_name = data_match.group(2)
                    cfg["external_data"].append({
                        "name": data_name,
                        "level": level,
                        "line": i,
                        "context": current_section or "DATA-DIVISION"
                    })

            # Detect SELECT statements (file sharing)
            if "SELECT" in line_upper and "ASSIGN" in line_upper:
                # SELECT FILE-NAME ASSIGN TO "physical-file"
                select_match = re.search(r'SELECT\s+([A-Z0-9\-]+)', line_upper)
                assign_match = re.search(r'ASSIGN\s+TO\s+["\']?([^"\'.\s]+)', line_upper)

                if select_match:
                    file_name = select_match.group(1)
                    physical_file = assign_match.group(1) if assign_match else None

                    cfg["file_sharing"].append({
                        "logical_name": file_name,
                        "physical_file": physical_file,
                        "line": i
                    })

        # Filter by section if specified
        if section_name:
            cfg = self._filter_cfg_by_section(cfg, section_name)

        return cfg

    def _filter_cfg_by_section(self, cfg: Dict[str, Any], section_name: str) -> Dict[str, Any]:
        """Filter CFG to show only specified section."""
        filtered = {
            "nodes": [n for n in cfg["nodes"] if n["name"] == section_name or
                     any(e["from"] == section_name for e in cfg["edges"])],
            "edges": [e for e in cfg["edges"] if e["from"] == section_name],
            "calls": [c for c in cfg["calls"] if c["from"] == section_name],
            "performs": [p for p in cfg["performs"] if p["from"] == section_name],
            "gotos": [g for g in cfg["gotos"] if g["from"] == section_name],
            "copybooks": [cb for cb in cfg["copybooks"] if cb["context"] == section_name],
            "dynamic_calls": [dc for dc in cfg["dynamic_calls"] if dc["from"] == section_name],
            "entry_points": [ep for ep in cfg["entry_points"] if ep["context"] == section_name],
            "external_data": cfg["external_data"],  # Keep all - global scope
            "file_sharing": cfg["file_sharing"]     # Keep all - global scope
        }
        return filtered

    def _format_cfg_as_dot(self, cfg: Dict[str, Any]) -> Dict[str, Any]:
        """Format CFG as Graphviz DOT format."""
        dot_lines = [
            "digraph COBOL_CFG {",
            "  rankdir=TB;",
            "  node [shape=box, style=rounded];"
        ]

        # Add nodes
        for node in cfg["nodes"]:
            node_id = node["name"].replace("-", "_")
            label = f"{node['name']} (L{node['line']})"
            shape = "rectangle" if node["type"] == "section" else "ellipse"
            dot_lines.append(f'  {node_id} [label="{label}", shape={shape}];')

        # Add edges
        for edge in cfg["edges"]:
            from_id = edge["from"].replace("-", "_")
            to_id = edge["to"].replace("-", "_")
            style = "dashed" if edge["type"] == "perform" else "solid"
            dot_lines.append(f'  {from_id} -> {to_id} [style={style}, label="{edge["type"]}"];')

        dot_lines.append("}")

        return {
            "format": "dot",
            "dot_source": "\n".join(dot_lines),
            "raw_cfg": cfg
        }

    def _format_cfg_as_arc(self, cfg: Dict[str, Any]) -> Dict[str, Any]:
        """Format CFG as arc diagram data."""
        # Arc diagram shows sections/paragraphs vertically with arcs showing flow
        nodes = sorted(cfg["nodes"], key=lambda n: n["line"])

        arcs = []
        for edge in cfg["edges"]:
            from_node = next((n for n in nodes if n["name"] == edge["from"]), None)
            to_node = next((n for n in nodes if n["name"] == edge["to"]), None)

            if from_node and to_node:
                arcs.append({
                    "from": edge["from"],
                    "to": edge["to"],
                    "from_line": from_node["line"],
                    "to_line": to_node["line"],
                    "type": edge["type"],
                    "direction": "forward" if to_node["line"] > from_node["line"] else "backward"
                })

        return {
            "format": "arc",
            "nodes": nodes,
            "arcs": arcs,
            "raw_cfg": cfg
        }

    def cleanup(self) -> None:
        """Cleanup all language server instances."""
        for lang, server in self._lsp_instances.items():
            try:
                # MultilsPy should handle cleanup
                pass
            except Exception as e:
                self.logger.log(f"Error cleaning up {lang} server: {e}", logging.ERROR)

        self._lsp_instances.clear()
        self._async_instances.clear()

        # Save session before cleanup
        try:
            self.save_session()
        except Exception as e:
            self.logger.log(f"Error saving session: {e}", logging.WARNING)