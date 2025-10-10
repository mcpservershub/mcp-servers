import logging
import os
import shutil
import tempfile
import time
from abc import abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

import pytest

from serena.symbol import CodeDiff
from solidlsp.ls_config import Language
from src.serena.symbol import SymbolManager
from test.conftest import create_ls, get_repo_path

pytestmark = pytest.mark.snapshot

log = logging.getLogger(__name__)


class EditingTest:
    def __init__(self, language: Language, rel_path: str):
        """
        :param language: the language
        :param rel_path: the relative path of the edited file
        """
        self.rel_path = rel_path
        self.language = language
        self.original_repo_path = get_repo_path(language)
        self.repo_path: Path | None = None

    @contextmanager
    def _setup(self) -> Iterator[SymbolManager]:
        """Context manager for setup/teardown with a temporary directory, providing the symbol manager."""
        temp_dir = Path(tempfile.mkdtemp())
        self.repo_path = temp_dir / self.original_repo_path.name
        language_server = None  # Initialize language_server
        try:
            print(f"Copying repo from {self.original_repo_path} to {self.repo_path}")
            shutil.copytree(self.original_repo_path, self.repo_path)
            # prevent deadlock on Windows due to file locks caused by antivirus or some other external software
            # wait for a long time here
            if os.name == "nt":
                time.sleep(0.1)
            log.info(f"Creating language server for {self.language} {self.rel_path}")
            language_server = create_ls(self.language, str(self.repo_path))
            log.info(f"Starting language server for {self.language} {self.rel_path}")
            language_server.start()
            log.info(f"Language server started for {self.language} {self.rel_path}")
            yield SymbolManager(lang_server=language_server)
        finally:
            if language_server is not None and language_server.is_running():
                log.info(f"Stopping language server for {self.language} {self.rel_path}")
                language_server.stop()
                # attempt at trigger of garbage collection
                language_server = None
                log.info(f"Language server stopped for {self.language} {self.rel_path}")

            # prevent deadlock on Windows due to lingering file locks
            if os.name == "nt":
                time.sleep(0.1)
            log.info(f"Removing temp directory {temp_dir}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            log.info(f"Temp directory {temp_dir} removed")

    def _read_file(self, rel_path: str) -> str:
        """Read the content of a file in the test repository."""
        assert self.repo_path is not None
        file_path = self.repo_path / rel_path
        with open(file_path, encoding="utf-8") as f:
            return f.read()

    def run_test(self, content_after_ground_truth: str) -> None:
        with self._setup() as symbol_manager:
            content_before = self._read_file(self.rel_path)
            self._apply_edit(symbol_manager)
            content_after = self._read_file(self.rel_path)
            code_diff = CodeDiff(self.rel_path, original_content=content_before, modified_content=content_after)
            self._test_diff(code_diff, content_after_ground_truth)

    @abstractmethod
    def _apply_edit(self, symbol_manager: SymbolManager) -> None:
        pass

    def _test_diff(self, code_diff: CodeDiff, snapshot: str) -> None:
        assert code_diff.modified_content == snapshot


# Python test file path
PYTHON_TEST_REL_FILE_PATH = os.path.join("test_repo", "variables.py")

# TypeScript test file path
TYPESCRIPT_TEST_FILE = "index.ts"


class DeleteSymbolTest(EditingTest):
    def __init__(self, language: Language, rel_path: str, deleted_symbol: str):
        super().__init__(language, rel_path)
        self.deleted_symbol = deleted_symbol
        self.rel_path = rel_path

    def _apply_edit(self, symbol_manager: SymbolManager) -> None:
        symbol_manager.delete_symbol(self.deleted_symbol, self.rel_path)


@pytest.mark.parametrize(
    "test_case",
    [
        pytest.param(
            DeleteSymbolTest(
                Language.PYTHON,
                PYTHON_TEST_REL_FILE_PATH,
                "VariableContainer",
            ),
            marks=pytest.mark.python,
        ),
        pytest.param(
            DeleteSymbolTest(
                Language.TYPESCRIPT,
                TYPESCRIPT_TEST_FILE,
                "DemoClass",
            ),
            marks=pytest.mark.typescript,
        ),
    ],
)
def test_delete_symbol(test_case, snapshot):
    test_case.run_test(content_after_ground_truth=snapshot)


NEW_PYTHON_FUNCTION = """def new_inserted_function():
    print("This is a new function inserted before another.")"""

NEW_PYTHON_CLASS_WITH_LEADING_NEWLINES = """

class NewInsertedClass:
    pass
"""

NEW_PYTHON_CLASS_WITH_TRAILING_NEWLINES = """class NewInsertedClass:
    pass


"""

NEW_TYPESCRIPT_FUNCTION = """function newInsertedFunction(): void {
    console.log("This is a new function inserted before another.");
}"""


NEW_PYTHON_VARIABLE = 'new_module_var = "Inserted after typed_module_var"'

NEW_TYPESCRIPT_FUNCTION_AFTER = """function newFunctionAfterClass(): void {
    console.log("This function is after DemoClass.");
}"""


class InsertInRelToSymbolTest(EditingTest):
    def __init__(
        self, language: Language, rel_path: str, symbol_name: str, new_content: str, mode: Literal["before", "after"] | None = None
    ):
        super().__init__(language, rel_path)
        self.symbol_name = symbol_name
        self.new_content = new_content
        self.mode: Literal["before", "after"] | None = mode

    def set_mode(self, mode: Literal["before", "after"]):
        self.mode = mode

    def _apply_edit(self, symbol_manager: SymbolManager) -> None:
        assert self.mode is not None
        if self.mode == "before":
            symbol_manager.insert_before_symbol(self.symbol_name, self.rel_path, self.new_content, use_same_indentation=False)
        elif self.mode == "after":
            symbol_manager.insert_after_symbol(self.symbol_name, self.rel_path, self.new_content, use_same_indentation=False)


@pytest.mark.parametrize("mode", ["before", "after"])
@pytest.mark.parametrize(
    "test_case",
    [
        pytest.param(
            InsertInRelToSymbolTest(
                Language.PYTHON,
                PYTHON_TEST_REL_FILE_PATH,
                "typed_module_var",
                NEW_PYTHON_VARIABLE,
            ),
            marks=pytest.mark.python,
        ),
        pytest.param(
            InsertInRelToSymbolTest(
                Language.PYTHON,
                PYTHON_TEST_REL_FILE_PATH,
                "use_module_variables",
                NEW_PYTHON_FUNCTION,
            ),
            marks=pytest.mark.python,
        ),
        pytest.param(
            InsertInRelToSymbolTest(
                Language.TYPESCRIPT,
                TYPESCRIPT_TEST_FILE,
                "DemoClass",
                NEW_TYPESCRIPT_FUNCTION_AFTER,
            ),
            marks=pytest.mark.typescript,
        ),
        pytest.param(
            InsertInRelToSymbolTest(
                Language.TYPESCRIPT,
                TYPESCRIPT_TEST_FILE,
                "helperFunction",
                NEW_TYPESCRIPT_FUNCTION,
            ),
            marks=pytest.mark.typescript,
        ),
    ],
)
def test_insert_in_rel_to_symbol(test_case: InsertInRelToSymbolTest, mode: Literal["before", "after"], snapshot):
    test_case.set_mode(mode)
    test_case.run_test(content_after_ground_truth=snapshot)


@pytest.mark.python
def test_insert_python_class_before(snapshot):
    InsertInRelToSymbolTest(
        Language.PYTHON,
        PYTHON_TEST_REL_FILE_PATH,
        "VariableDataclass",
        NEW_PYTHON_CLASS_WITH_TRAILING_NEWLINES,
        mode="before",
    ).run_test(snapshot)


@pytest.mark.python
def test_insert_python_class_after(snapshot):
    InsertInRelToSymbolTest(
        Language.PYTHON,
        PYTHON_TEST_REL_FILE_PATH,
        "VariableDataclass",
        NEW_PYTHON_CLASS_WITH_LEADING_NEWLINES,
        mode="after",
    ).run_test(snapshot)


PYTHON_REPLACED_BODY = """def modify_instance_var(self):
        # This body has been replaced
        self.instance_var = "Replaced!"
        self.reassignable_instance_var = 999
"""

TYPESCRIPT_REPLACED_BODY = """function printValue() {
        // This body has been replaced
        console.warn("New value: " + this.value);
    }
"""


class ReplaceBodyTest(EditingTest):
    def __init__(self, language: Language, rel_path: str, symbol_name: str, new_body: str):
        super().__init__(language, rel_path)
        self.symbol_name = symbol_name
        self.new_body = new_body

    def _apply_edit(self, symbol_manager: SymbolManager) -> None:
        symbol_manager.replace_body(self.symbol_name, self.rel_path, self.new_body, use_same_indentation=False)


@pytest.mark.parametrize(
    "test_case",
    [
        pytest.param(
            ReplaceBodyTest(
                Language.PYTHON,
                PYTHON_TEST_REL_FILE_PATH,
                "VariableContainer/modify_instance_var",
                PYTHON_REPLACED_BODY,
            ),
            marks=pytest.mark.python,
        ),
        pytest.param(
            ReplaceBodyTest(
                Language.TYPESCRIPT,
                TYPESCRIPT_TEST_FILE,
                "DemoClass/printValue",
                TYPESCRIPT_REPLACED_BODY,
            ),
            marks=pytest.mark.typescript,
        ),
    ],
)
def test_replace_body(test_case: ReplaceBodyTest, snapshot):
    test_case.run_test(content_after_ground_truth=snapshot)
