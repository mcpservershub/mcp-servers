import logging
import re
from typing import TYPE_CHECKING, Any

from llm_sandbox.const import SupportedLanguage
from llm_sandbox.data import PlotOutput

from .base import AbstractLanguageHandler, LanguageConfig

if TYPE_CHECKING:
    from .base import ContainerProtocol


class CSharpHandler(AbstractLanguageHandler):
    """Handler for C#."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initialize the C# handler."""
        super().__init__(logger)

        self.config = LanguageConfig(
            name=SupportedLanguage.CSHARP,
            file_extension="cs",
            execution_commands=["dotnet run --project {file}"],
            package_manager="dotnet add package",
            plot_detection=None,
            is_support_library_installation=True,
        )

    def inject_plot_detection_code(self, code: str) -> str:
        """C# does not support plot detection directly in this manner."""
        return code

    def run_with_artifacts(
        self,
        container: "ContainerProtocol",
        code: str,
        libraries: list | None = None,
        enable_plotting: bool = True,  # noqa: ARG002
        output_dir: str = "/tmp/sandbox_plots",  # noqa: ARG002
        timeout: int = 30,
    ) -> tuple[Any, list[PlotOutput]]:
        """Run C# code without artifact extraction.

        C# plot detection is not currently supported. This method
        runs the code normally and returns an empty list of plots.

        Future implementations could support:
        - OxyPlot for chart generation
        - LiveCharts for plotting
        - System.Drawing for graphics

        Args:
            container: The container protocol instance to run code in
            code: The C# code to execute
            libraries: Optional list of libraries to install before running
            enable_plotting: Whether to enable plot detection (ignored for C#)
            output_dir: Directory where plots should be saved (unused)
            timeout: Timeout for the code execution

        Returns:
            tuple: (execution_result, empty_list_of_plots)

        """
        self.logger.warning("C# does not support plot extraction yet")
        result = container.run(code, libraries, timeout=timeout)
        return result, []

    def get_import_patterns(self, module: str) -> str:
        """Get the regex patterns for using statements.

        Regex to match using statements for the given namespace.
        Covers:
            using Module.Class;
            using Module.Namespace;
            using static Module.Class;
            using alias = Module.Class;
        Handles variations in whitespace.
        Negative lookbehind and lookahead to avoid matching comments or parts of other words.

        Args:
            module (str): The name of the namespace to get using patterns for.
                        Can be a full path like System.Collections.Generic

        Returns:
            str: The regex patterns for using statements.

        """
        # C# namespaces can have dots, need to escape them for regex
        # Module can be something like "System.Collections" or "System.Collections.Generic"
        # We want to match "using System.Collections.Generic;" or "using static System.Collections.Generic;"
        # or "using alias = System.Collections.Generic;"
        escaped_module = re.escape(module)
        return rf"(?:^|\s)using(?:\s+static)?\s+(?:\w+\s*=\s*)?{escaped_module}(?:\.\w+)*\s*;(?=[\s\S]|$)"

    @staticmethod
    def get_multiline_comment_patterns() -> str:
        """Get the regex patterns for multiline comments.

        Regex to match multiline comments.
        Handles variations in whitespace.
        """
        return r"/\*[\s\S]*?\*/"

    @staticmethod
    def get_inline_comment_patterns() -> str:
        """Get the regex patterns for inline comments.

        Regex to match inline comments.
        Handles variations in whitespace.
        """
        return r"//.*$"