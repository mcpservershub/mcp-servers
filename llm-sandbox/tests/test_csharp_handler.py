# ruff: noqa: SLF001, PLR2004

import logging
import re
from unittest.mock import MagicMock

from llm_sandbox.const import SupportedLanguage
from llm_sandbox.language_handlers.csharp_handler import CSharpHandler


class TestCSharpHandler:
    """Test CSharpHandler specific functionality."""

    def test_init(self) -> None:
        """Test CSharpHandler initialization."""
        handler = CSharpHandler()

        assert handler.config.name == SupportedLanguage.CSHARP
        assert handler.config.file_extension == "cs"
        assert "dotnet run --project {file}" in handler.config.execution_commands
        assert handler.config.package_manager == "dotnet add package"
        assert handler.config.plot_detection is None
        assert handler.config.is_support_library_installation is True

    def test_init_with_custom_logger(self) -> None:
        """Test CSharpHandler initialization with custom logger."""
        custom_logger = logging.getLogger("custom")
        handler = CSharpHandler(custom_logger)
        assert handler.logger == custom_logger

    def test_inject_plot_detection_code(self) -> None:
        """Test plot detection code injection (should return unchanged code)."""
        handler = CSharpHandler()
        code = 'Console.WriteLine("Hello World");'

        injected_code = handler.inject_plot_detection_code(code)

        assert injected_code == code  # Should be unchanged since C# doesn't support plot detection

    def test_run_with_artifacts_no_plotting_support(self) -> None:
        """Test run_with_artifacts returns empty plots list."""
        handler = CSharpHandler()
        mock_container = MagicMock()
        mock_result = MagicMock()
        mock_container.run.return_value = mock_result

        result, plots = handler.run_with_artifacts(
            container=mock_container,
            code='Console.WriteLine("Hello");',
            libraries=None,
            enable_plotting=True,
            timeout=30,
            output_dir="/tmp/sandbox_plots",
        )

        assert result == mock_result
        assert plots == []
        mock_container.run.assert_called_once_with('Console.WriteLine("Hello");', None, timeout=30)

    def test_extract_plots_returns_empty(self) -> None:
        """Test extract_plots returns empty list."""
        handler = CSharpHandler()
        mock_container = MagicMock()

        plots = handler.extract_plots(mock_container, "/tmp/sandbox_plots")

        assert plots == []

    def test_get_import_patterns(self) -> None:
        """Test get_import_patterns method."""
        handler = CSharpHandler()

        # Test basic namespace using
        pattern = handler.get_import_patterns("System.Collections")

        # Should match various using formats
        using_code_samples = [
            "using System.Collections;",
            "using System.Collections.Generic;",
            "using static System.Collections.Generic.List;",
            "using MyList = System.Collections.Generic.List;",
            "  using System.Collections.Concurrent;  ",
        ]

        for code in using_code_samples:
            if "System.Collections" in code:
                assert re.search(pattern, code), f"Pattern should match: {code}"

        # Test specific namespace using
        generic_pattern = handler.get_import_patterns("System.Collections.Generic")
        assert re.search(generic_pattern, "using System.Collections.Generic;")
        assert re.search(generic_pattern, "using static System.Collections.Generic.List;")

        # Should not match comments or parts of other words
        non_matching_samples = [
            "// using System.Collections;",
            "/* using System.Collections; */",
            "using System.CollectionUtils;",
            "using MySystem.Collections;",
        ]

        for code in non_matching_samples:
            filtered_code = handler.filter_comments(code)
            assert not re.search(pattern, filtered_code), f"Pattern should not match: {code}"

    def test_get_multiline_comment_patterns(self) -> None:
        """Test get_multiline_comment_patterns method."""
        pattern = CSharpHandler.get_multiline_comment_patterns()

        comment_samples = [
            "/* This is a comment */",
            "/*\n * Multiline\n * comment\n */",
            "/* Single line with content */",
            "/**\n * XML doc comment\n */",
        ]

        for comment in comment_samples:
            assert re.search(pattern, comment), f"Pattern should match: {comment}"

    def test_get_inline_comment_patterns(self) -> None:
        """Test get_inline_comment_patterns method."""
        pattern = CSharpHandler.get_inline_comment_patterns()

        comment_samples = [
            "// This is a comment",
            'Console.WriteLine("Hello");  // Inline comment',
            "    // Indented comment",
            "int x = 5; // Variable definition",
        ]

        for comment in comment_samples:
            assert re.search(pattern, comment), f"Pattern should match: {comment}"

    def test_filter_comments(self) -> None:
        """Test comment filtering functionality."""
        handler = CSharpHandler()

        code_with_comments = """
        // This is a single line comment
        public class Test {
            /* This is a
               multiline comment */
            public static void Main(string[] args) {
                Console.WriteLine("Hello"); // Inline comment
            }
        }
        """

        filtered_code = handler.filter_comments(code_with_comments)

        # Should remove comments but keep code
        assert 'Console.WriteLine("Hello");' in filtered_code
        assert "public class Test" in filtered_code
        assert "// This is a single line comment" not in filtered_code
        assert "/* This is a" not in filtered_code
        assert "// Inline comment" not in filtered_code

    def test_properties(self) -> None:
        """Test handler property methods."""
        handler = CSharpHandler()

        assert handler.name == SupportedLanguage.CSHARP
        assert handler.file_extension == "cs"
        assert handler.supported_plot_libraries == []
        assert handler.is_support_library_installation is True
        assert handler.is_support_plot_detection is False

    def test_get_execution_commands(self) -> None:
        """Test getting execution commands."""
        handler = CSharpHandler()

        commands = handler.get_execution_commands("Test.csproj")

        assert len(commands) == 1
        assert commands[0] == "dotnet run --project Test.csproj"

    def test_get_library_installation_command(self) -> None:
        """Test getting library installation command."""
        handler = CSharpHandler()

        command = handler.get_library_installation_command("Newtonsoft.Json")

        assert command == "dotnet add package Newtonsoft.Json"

    def test_complex_import_patterns(self) -> None:
        """Test more complex using scenarios."""
        handler = CSharpHandler()

        # Test nested namespace usings
        pattern = handler.get_import_patterns("System.Text")

        complex_usings = [
            "using System.Text;",
            "using System.Text.Json;",
            "using static System.Text.Encoding;",
            "using Encoder = System.Text.Encoding;",
        ]

        for using_stmt in complex_usings:
            if "System.Text" in using_stmt:
                assert re.search(pattern, using_stmt), f"Should match: {using_stmt}"