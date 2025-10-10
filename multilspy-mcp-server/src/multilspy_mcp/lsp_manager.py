"""
LSP Manager - Wrapper around MultilsPy for managing Language Server instances.
"""

import os
import json
import asyncio
import logging
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
            with self.start_sync_server(language) as server:
                results = server.request_workspace_symbol(query)
                return [self._convert_symbol(sym) for sym in (results or [])]
        
        # Otherwise, search across all initialized languages
        all_symbols = []
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