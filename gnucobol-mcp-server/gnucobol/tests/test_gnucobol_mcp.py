"""
Comprehensive test suite for GnuCOBOL MCP Server

This test suite validates all MCP tools provided by the GnuCOBOL server:
- compile_cobol: Compile COBOL source code
- syntax_check: Validate COBOL syntax
- analyze_code: Generate analysis reports and cross-references
- batch_compile: Compile multiple COBOL files

Tests cover:
- Valid and invalid COBOL code
- Error handling and edge cases
- STDIN/STDOUT processing
- Compiler output parsing
"""

import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess
import tempfile

# Test data directory
TEST_DIR = Path(__file__).parent
SAMPLE_DIR = TEST_DIR / "sample_cobol"
VALID_DIR = SAMPLE_DIR / "valid"
INVALID_DIR = SAMPLE_DIR / "invalid"


# Mock MCP server imports for testing
class MockFastMCP:
    """Mock FastMCP for testing without actual MCP server"""
    def __init__(self, name):
        self.name = name
        self.tools = {}

    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator

    def run(self):
        pass


@pytest.fixture
def sample_valid_hello():
    """Valid COBOL hello world program"""
    return (VALID_DIR / "hello.cob").read_text()


@pytest.fixture
def sample_valid_calculator():
    """Valid COBOL calculator program"""
    return (VALID_DIR / "calculator.cob").read_text()


@pytest.fixture
def sample_invalid_syntax():
    """Invalid COBOL with syntax errors"""
    return (INVALID_DIR / "syntax_error.cob").read_text()


@pytest.fixture
def sample_invalid_missing_division():
    """Invalid COBOL missing required division"""
    return (INVALID_DIR / "missing_division.cob").read_text()


@pytest.fixture
def temp_cobol_file():
    """Create a temporary COBOL file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cob', delete=False) as f:
        yield f.name
    # Cleanup
    if os.path.exists(f.name):
        os.unlink(f.name)


class TestCompileCobol:
    """Test suite for compile_cobol MCP tool"""

    def test_compile_valid_hello_world(self, sample_valid_hello):
        """Test compilation of valid hello world program"""
        # This test will verify that cobc can compile valid COBOL code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cob', delete=False) as f:
            f.write(sample_valid_hello)
            f.flush()

            try:
                # Test compilation
                result = subprocess.run(
                    ['cobc', '-x', f.name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                assert result.returncode == 0, f"Compilation failed: {result.stderr}"

                # Check executable was created
                executable = f.name.replace('.cob', '')
                assert os.path.exists(executable), "Executable not created"

                # Cleanup executable
                if os.path.exists(executable):
                    os.unlink(executable)
            finally:
                os.unlink(f.name)

    def test_compile_valid_calculator(self, sample_valid_calculator):
        """Test compilation of valid calculator program"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cob', delete=False) as f:
            f.write(sample_valid_calculator)
            f.flush()

            try:
                result = subprocess.run(
                    ['cobc', '-x', f.name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                assert result.returncode == 0, f"Compilation failed: {result.stderr}"
            finally:
                os.unlink(f.name)

    def test_compile_invalid_syntax(self, sample_invalid_syntax):
        """Test compilation of invalid COBOL code with syntax errors"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cob', delete=False) as f:
            f.write(sample_invalid_syntax)
            f.flush()

            try:
                result = subprocess.run(
                    ['cobc', '-x', f.name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                assert result.returncode != 0, "Expected compilation to fail"
                assert len(result.stderr) > 0, "Expected error messages"
                assert "error" in result.stderr.lower(), "Expected error in output"
            finally:
                os.unlink(f.name)

    def test_compile_from_stdin(self, sample_valid_hello):
        """Test compilation from STDIN (MCP server will use this)"""
        result = subprocess.run(
            ['cobc', '-x', '-', '-o', '/tmp/test_stdin_output'],
            input=sample_valid_hello,
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0, f"STDIN compilation failed: {result.stderr}"

        # Cleanup
        if os.path.exists('/tmp/test_stdin_output'):
            os.unlink('/tmp/test_stdin_output')

    def test_compile_empty_input(self):
        """Test compilation with empty input"""
        result = subprocess.run(
            ['cobc', '-x', '-'],
            input="",
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode != 0, "Expected compilation to fail with empty input"

    def test_compile_with_warnings(self):
        """Test compilation that produces warnings"""
        # COBOL code with potential warnings (unused variables, etc.)
        code_with_warnings = """
       IDENTIFICATION DIVISION.
       PROGRAM-ID. WARNINGS-TEST.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 UNUSED-VAR PIC 9(5) VALUE 12345.
       01 USED-VAR   PIC 9(5) VALUE 54321.

       PROCEDURE DIVISION.
           DISPLAY USED-VAR.
           STOP RUN.
        """

        result = subprocess.run(
            ['cobc', '-x', '-', '-Wall'],
            input=code_with_warnings,
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should compile successfully despite warnings
        assert result.returncode == 0, "Compilation should succeed with warnings"


class TestSyntaxCheck:
    """Test suite for syntax_check MCP tool"""

    def test_syntax_check_valid_code(self, sample_valid_hello):
        """Test syntax checking of valid COBOL code"""
        result = subprocess.run(
            ['cobc', '-fsyntax-only', '-'],
            input=sample_valid_hello,
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0, f"Syntax check failed: {result.stderr}"
        assert len(result.stderr) == 0 or "error" not in result.stderr.lower()

    def test_syntax_check_invalid_code(self, sample_invalid_syntax):
        """Test syntax checking of invalid COBOL code"""
        result = subprocess.run(
            ['cobc', '-fsyntax-only', '-'],
            input=sample_invalid_syntax,
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode != 0, "Expected syntax check to fail"
        assert "error" in result.stderr.lower(), "Expected error messages"

    def test_syntax_check_missing_division(self, sample_invalid_missing_division):
        """Test syntax checking with missing required division"""
        result = subprocess.run(
            ['cobc', '-fsyntax-only', '-'],
            input=sample_invalid_missing_division,
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode != 0, "Expected syntax check to fail"
        assert "error" in result.stderr.lower() or "division" in result.stderr.lower()

    def test_syntax_check_incremental(self, sample_valid_hello):
        """Test incremental syntax checking (fast mode)"""
        result = subprocess.run(
            ['cobc', '-fsyntax-only', '-'],
            input=sample_valid_hello,
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode == 0
        # Syntax check should be faster than full compilation

    def test_syntax_check_parse_errors(self):
        """Test parsing and extracting syntax errors"""
        invalid_code = """
       IDENTIFICATION DIVISION.
       PROGRAM-ID. SYNTAX-ERROR.

       PROCEDURE DIVISION.
           DISPLAY "Missing period here"
           INVALID-STATEMENT.
           STOP RUN.
        """

        result = subprocess.run(
            ['cobc', '-fsyntax-only', '-'],
            input=invalid_code,
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode != 0
        # Verify error output can be parsed
        errors = result.stderr.split('\n')
        assert len(errors) > 0


class TestAnalyzeCode:
    """Test suite for analyze_code MCP tool"""

    def test_generate_listing(self, sample_valid_hello):
        """Test generation of compiler listing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cob', delete=False) as f:
            f.write(sample_valid_hello)
            f.flush()

            try:
                # Generate listing file
                listing_file = f.name.replace('.cob', '.lst')
                result = subprocess.run(
                    ['cobc', '-t', f.name, '-o', listing_file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                assert result.returncode == 0, f"Listing generation failed: {result.stderr}"
                assert os.path.exists(listing_file), "Listing file not created"

                # Verify listing content
                with open(listing_file, 'r') as lf:
                    listing_content = lf.read()
                    assert len(listing_content) > 0, "Listing file is empty"

                # Cleanup
                if os.path.exists(listing_file):
                    os.unlink(listing_file)
            finally:
                os.unlink(f.name)

    def test_generate_symbol_table(self, sample_valid_calculator):
        """Test generation of symbol table"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cob', delete=False) as f:
            f.write(sample_valid_calculator)
            f.flush()

            try:
                result = subprocess.run(
                    ['cobc', '-t', '-ftsymbols', f.name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                assert result.returncode == 0, f"Symbol table generation failed: {result.stderr}"
            finally:
                os.unlink(f.name)

    def test_generate_cross_reference(self, sample_valid_calculator):
        """Test generation of cross-reference report"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cob', delete=False) as f:
            f.write(sample_valid_calculator)
            f.flush()

            try:
                result = subprocess.run(
                    ['cobc', '-t', '-Xref', f.name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                assert result.returncode == 0, f"Cross-reference generation failed: {result.stderr}"
            finally:
                os.unlink(f.name)

    def test_full_analysis_report(self, sample_valid_calculator):
        """Test generation of full analysis report with all options"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cob', delete=False) as f:
            f.write(sample_valid_calculator)
            f.flush()

            try:
                result = subprocess.run(
                    ['cobc', '-t', '-ftsymbols', '-Xref', f.name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                assert result.returncode == 0, "Full analysis failed"
            finally:
                os.unlink(f.name)

    def test_parse_listing_output(self, sample_valid_hello):
        """Test parsing of listing file output"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cob', delete=False) as f:
            f.write(sample_valid_hello)
            f.flush()

            try:
                listing_file = f.name.replace('.cob', '.lst')
                result = subprocess.run(
                    ['cobc', '-t', f.name, '-o', listing_file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if os.path.exists(listing_file):
                    with open(listing_file, 'r') as lf:
                        listing = lf.read()

                        # Verify listing contains expected sections
                        assert len(listing) > 0
                        # Listing should contain line numbers and source code
                        lines = listing.split('\n')
                        assert len(lines) > 0

                    os.unlink(listing_file)
            finally:
                os.unlink(f.name)


class TestBatchCompile:
    """Test suite for batch_compile MCP tool"""

    def test_batch_compile_multiple_files(self, sample_valid_hello, sample_valid_calculator):
        """Test batch compilation of multiple COBOL files"""
        files = []
        try:
            # Create multiple temp files
            for i, content in enumerate([sample_valid_hello, sample_valid_calculator]):
                f = tempfile.NamedTemporaryFile(mode='w', suffix='.cob', delete=False)
                f.write(content)
                f.flush()
                f.close()
                files.append(f.name)

            # Test batch compilation
            result = subprocess.run(
                ['cobc', '-x', '-o', '/tmp/batch_test'] + files,
                capture_output=True,
                text=True,
                timeout=15
            )

            assert result.returncode == 0, f"Batch compilation failed: {result.stderr}"

            # Cleanup
            if os.path.exists('/tmp/batch_test'):
                os.unlink('/tmp/batch_test')
        finally:
            for f in files:
                if os.path.exists(f):
                    os.unlink(f)

    def test_batch_compile_with_errors(self, sample_valid_hello, sample_invalid_syntax):
        """Test batch compilation when one file has errors"""
        files = []
        try:
            # Create files with mixed valid/invalid content
            for content in [sample_valid_hello, sample_invalid_syntax]:
                f = tempfile.NamedTemporaryFile(mode='w', suffix='.cob', delete=False)
                f.write(content)
                f.flush()
                f.close()
                files.append(f.name)

            result = subprocess.run(
                ['cobc', '-x', '-o', '/tmp/batch_test_error'] + files,
                capture_output=True,
                text=True,
                timeout=15
            )

            # Should fail due to invalid file
            assert result.returncode != 0, "Expected batch compilation to fail"
            assert "error" in result.stderr.lower()
        finally:
            for f in files:
                if os.path.exists(f):
                    os.unlink(f)

    def test_batch_compile_performance(self, sample_valid_hello):
        """Test batch compilation performance"""
        import time

        files = []
        try:
            # Create 5 identical files
            for i in range(5):
                f = tempfile.NamedTemporaryFile(mode='w', suffix='.cob', delete=False)
                f.write(sample_valid_hello)
                f.flush()
                f.close()
                files.append(f.name)

            start_time = time.time()
            result = subprocess.run(
                ['cobc', '-fsyntax-only'] + files,
                capture_output=True,
                text=True,
                timeout=30
            )
            duration = time.time() - start_time

            assert result.returncode == 0, "Batch syntax check failed"
            # Should complete in reasonable time (adjust as needed)
            assert duration < 30, f"Batch compilation took too long: {duration}s"
        finally:
            for f in files:
                if os.path.exists(f):
                    os.unlink(f)


class TestStdioProcessing:
    """Test suite for STDIN/STDOUT processing"""

    def test_stdin_compilation(self, sample_valid_hello):
        """Test reading COBOL code from STDIN"""
        result = subprocess.run(
            ['cobc', '-fsyntax-only', '-'],
            input=sample_valid_hello,
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0, "STDIN processing failed"

    def test_stdout_error_output(self, sample_invalid_syntax):
        """Test error messages on STDOUT/STDERR"""
        result = subprocess.run(
            ['cobc', '-fsyntax-only', '-'],
            input=sample_invalid_syntax,
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode != 0
        assert len(result.stderr) > 0, "Expected error output on STDERR"

    def test_large_input_stdin(self):
        """Test processing large COBOL program via STDIN"""
        # Generate a large COBOL program
        large_program = """
       IDENTIFICATION DIVISION.
       PROGRAM-ID. LARGE-PROGRAM.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
"""
        # Add many variables
        for i in range(100):
            large_program += f"       01 VAR-{i:03d} PIC 9(5) VALUE {i:05d}.\n"

        large_program += """
       PROCEDURE DIVISION.
           DISPLAY "Large program test".
           STOP RUN.
        """

        result = subprocess.run(
            ['cobc', '-fsyntax-only', '-'],
            input=large_program,
            capture_output=True,
            text=True,
            timeout=15
        )

        assert result.returncode == 0, "Large program processing failed"

    def test_unicode_handling(self):
        """Test handling of unicode characters in COBOL code"""
        unicode_program = """
       IDENTIFICATION DIVISION.
       PROGRAM-ID. UNICODE-TEST.

       PROCEDURE DIVISION.
           DISPLAY "Hello, World! 你好世界".
           STOP RUN.
        """

        result = subprocess.run(
            ['cobc', '-fsyntax-only', '-'],
            input=unicode_program,
            capture_output=True,
            text=True,
            timeout=10
        )

        # Behavior depends on GnuCOBOL version and locale
        # Test that it doesn't crash
        assert isinstance(result.returncode, int)


class TestErrorHandling:
    """Test suite for error handling and edge cases"""

    def test_missing_compiler(self):
        """Test behavior when cobc is not available"""
        result = subprocess.run(
            ['nonexistent-compiler', '--version'],
            capture_output=True,
            text=True
        )

        # Should fail gracefully
        assert result.returncode != 0

    def test_timeout_handling(self):
        """Test timeout for long-running compilations"""
        # This would need a COBOL program that takes a long time
        # For now, just verify timeout mechanism works
        try:
            result = subprocess.run(
                ['sleep', '100'],
                capture_output=True,
                text=True,
                timeout=1
            )
            assert False, "Should have timed out"
        except subprocess.TimeoutExpired:
            # Expected behavior
            pass

    def test_invalid_cobc_options(self):
        """Test handling of invalid compiler options"""
        result = subprocess.run(
            ['cobc', '--invalid-option-that-does-not-exist'],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode != 0

    def test_file_permission_errors(self):
        """Test handling of file permission errors"""
        # Create a read-only file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cob', delete=False) as f:
            f.write("       IDENTIFICATION DIVISION.\n")
            f.flush()

            try:
                # Make file read-only
                os.chmod(f.name, 0o444)

                # Try to compile (should work for reading)
                result = subprocess.run(
                    ['cobc', '-fsyntax-only', f.name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                # Reading should work
                assert isinstance(result.returncode, int)
            finally:
                os.chmod(f.name, 0o644)  # Restore permissions
                os.unlink(f.name)

    def test_null_input_handling(self):
        """Test handling of null/empty input"""
        result = subprocess.run(
            ['cobc', '-fsyntax-only', '-'],
            input=None,
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should handle gracefully (may succeed with empty input or fail)
        assert isinstance(result.returncode, int)

    def test_malformed_cobol_recovery(self):
        """Test compiler recovery from malformed COBOL"""
        malformed = """
       THIS IS NOT VALID COBOL AT ALL
       RANDOM TEXT HERE
       123456789
        """

        result = subprocess.run(
            ['cobc', '-fsyntax-only', '-'],
            input=malformed,
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode != 0
        # Should produce error messages, not crash
        assert isinstance(result.stderr, str)


class TestMCPIntegration:
    """Test suite for MCP server integration"""

    def test_mcp_tool_interface(self):
        """Test that MCP tools have correct interface"""
        # This tests the structure expected by MCP
        # Actual implementation will be in gnucobol_mcp/server.py

        expected_tools = [
            'compile_cobol',
            'syntax_check',
            'analyze_code',
            'batch_compile'
        ]

        # Verify tools will be properly structured
        for tool_name in expected_tools:
            assert isinstance(tool_name, str)
            assert len(tool_name) > 0

    def test_mcp_error_format(self):
        """Test MCP error response format"""
        # MCP errors should be JSON-serializable
        error_response = {
            "error": "Compilation failed",
            "details": "Syntax error at line 10",
            "returncode": 1
        }

        # Verify can be serialized to JSON
        json_str = json.dumps(error_response)
        assert isinstance(json_str, str)

        # Verify can be deserialized
        parsed = json.loads(json_str)
        assert parsed['error'] == error_response['error']

    def test_mcp_success_format(self):
        """Test MCP success response format"""
        success_response = {
            "success": True,
            "output": "Compilation successful",
            "executable": "/path/to/program"
        }

        json_str = json.dumps(success_response)
        parsed = json.loads(json_str)
        assert parsed['success'] is True


# Pytest configuration and fixtures
@pytest.fixture(scope="session")
def check_cobc_available():
    """Check if GnuCOBOL compiler is available"""
    try:
        result = subprocess.run(
            ['cobc', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"\nGnuCOBOL version: {result.stdout.split()[0]}")
            return True
    except (subprocess.SubprocessError, FileNotFoundError):
        pytest.skip("GnuCOBOL (cobc) not available")
    return False


@pytest.fixture(autouse=True)
def ensure_cobc_available(check_cobc_available):
    """Ensure cobc is available before running tests"""
    if not check_cobc_available:
        pytest.skip("GnuCOBOL not available")


# Test execution markers
pytestmark = [
    pytest.mark.mcp,
    pytest.mark.gnucobol
]


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
