"""
Tests for Skim MCP Server

These tests verify the functionality of the MCP tools provided by the server.
"""

import pytest
import subprocess
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from skim_mcp_server.server import (
    check_sk_installed,
    run_sk_command,
    fuzzy_find_files,
    fuzzy_search_content,
    fuzzy_filter_lines,
    fuzzy_select_git_files,
    interactive_search,
)


class TestCheckSkInstalled:
    """Test sk installation check."""

    def test_check_sk_installed_when_available(self):
        """Test that check returns True when sk is available."""
        with patch('shutil.which', return_value='/usr/bin/sk'):
            assert check_sk_installed() is True

    def test_check_sk_installed_when_not_available(self):
        """Test that check returns False when sk is not available."""
        with patch('shutil.which', return_value=None):
            assert check_sk_installed() is False


class TestRunSkCommand:
    """Test run_sk_command function."""

    def test_run_sk_command_not_installed(self):
        """Test behavior when sk is not installed."""
        with patch('skim_mcp_server.server.check_sk_installed', return_value=False):
            result = run_sk_command(input_data="test")
            assert result['success'] is False
            assert 'not installed' in result['error']
            assert result['exit_code'] == -1

    def test_run_sk_command_timeout(self):
        """Test behavior when command times out."""
        with patch('skim_mcp_server.server.check_sk_installed', return_value=True):
            with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('sk', 1)):
                result = run_sk_command(input_data="test", timeout=1)
                assert result['success'] is False
                assert 'timed out' in result['error']
                assert result['exit_code'] == -1

    def test_run_sk_command_success(self):
        """Test successful sk command execution."""
        with patch('skim_mcp_server.server.check_sk_installed', return_value=True):
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "file1.txt\nfile2.txt\n"
            mock_result.stderr = ""

            with patch('subprocess.run', return_value=mock_result):
                result = run_sk_command(input_data="test\ndata")
                assert result['success'] is True
                assert len(result['selections']) == 2
                assert result['selections'][0] == "file1.txt"
                assert result['selections'][1] == "file2.txt"
                assert result['exit_code'] == 0

    def test_run_sk_command_aborted(self):
        """Test behavior when user aborts (Ctrl-C)."""
        with patch('skim_mcp_server.server.check_sk_installed', return_value=True):
            mock_result = MagicMock()
            mock_result.returncode = 130  # Aborted
            mock_result.stdout = ""
            mock_result.stderr = ""

            with patch('subprocess.run', return_value=mock_result):
                result = run_sk_command(input_data="test")
                assert result['success'] is False
                assert result['exit_code'] == 130
                assert result['error'] is None  # No error for abort

    def test_run_sk_command_with_options(self):
        """Test sk command with various options."""
        with patch('skim_mcp_server.server.check_sk_installed', return_value=True):
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "result\n"
            mock_result.stderr = ""

            with patch('subprocess.run', return_value=mock_result) as mock_run:
                result = run_sk_command(
                    input_data="test",
                    query="search",
                    multi=True,
                    regex=True,
                    exact=True,
                    case_sensitive=True,
                )

                # Verify command was called with correct arguments
                call_args = mock_run.call_args
                cmd = call_args[0][0]
                assert 'sk' in cmd
                assert '--query' in cmd
                assert 'search' in cmd
                assert '--multi' in cmd
                assert '--regex' in cmd
                assert '--exact' in cmd
                assert '--case-sensitive' in cmd


class TestFuzzyFindFiles:
    """Test fuzzy_find_files tool."""

    def test_fuzzy_find_files_with_fd(self):
        """Test file finding with fd available."""
        with patch('shutil.which') as mock_which:
            # fd is available
            mock_which.side_effect = lambda x: '/usr/bin/fd' if x == 'fd' else None

            with patch('subprocess.run') as mock_run:
                # Mock fd output
                fd_result = MagicMock()
                fd_result.returncode = 0
                fd_result.stdout = "file1.py\nfile2.py\n"

                # Mock sk output
                sk_result = MagicMock()
                sk_result.returncode = 0
                sk_result.stdout = "file1.py\n"
                sk_result.stderr = ""

                mock_run.side_effect = [fd_result, sk_result]

                with patch('skim_mcp_server.server.check_sk_installed', return_value=True):
                    result = fuzzy_find_files(directory=".", query="file1")

                    assert result['success'] is True
                    assert len(result['selections']) == 1
                    assert result['selections'][0] == "file1.py"

    def test_fuzzy_find_files_fallback_to_find(self):
        """Test file finding fallback to find when fd is not available."""
        with patch('shutil.which') as mock_which:
            # fd is not available, but bat is
            mock_which.side_effect = lambda x: '/usr/bin/bat' if x == 'bat' else None

            with patch('subprocess.run') as mock_run:
                # Mock find output
                find_result = MagicMock()
                find_result.returncode = 0
                find_result.stdout = "./file1.txt\n./file2.txt\n"

                # Mock sk output
                sk_result = MagicMock()
                sk_result.returncode = 0
                sk_result.stdout = "./file1.txt\n"
                sk_result.stderr = ""

                mock_run.side_effect = [find_result, sk_result]

                with patch('skim_mcp_server.server.check_sk_installed', return_value=True):
                    result = fuzzy_find_files(directory=".", query="file1")

                    assert result['success'] is True
                    assert len(result['selections']) == 1

    def test_fuzzy_find_files_with_options(self):
        """Test file finding with various options."""
        with patch('shutil.which', return_value='/usr/bin/fd'):
            with patch('subprocess.run') as mock_run:
                fd_result = MagicMock()
                fd_result.returncode = 0
                fd_result.stdout = "test.py\n"

                sk_result = MagicMock()
                sk_result.returncode = 0
                sk_result.stdout = "test.py\n"
                sk_result.stderr = ""

                mock_run.side_effect = [fd_result, sk_result]

                with patch('skim_mcp_server.server.check_sk_installed', return_value=True):
                    result = fuzzy_find_files(
                        directory=".",
                        query="test",
                        file_types="py,js",
                        hidden=True,
                        max_depth=3,
                    )

                    # Verify fd was called with correct arguments
                    fd_call = mock_run.call_args_list[0][0][0]
                    assert '--extension' in fd_call
                    assert '--hidden' in fd_call
                    assert '--max-depth' in fd_call


class TestFuzzySearchContent:
    """Test fuzzy_search_content tool."""

    def test_fuzzy_search_content_with_ripgrep(self):
        """Test content search with ripgrep."""
        with patch('shutil.which') as mock_which:
            mock_which.side_effect = lambda x: f'/usr/bin/{x}' if x in ['rg', 'bat'] else None

            with patch('subprocess.run') as mock_run:
                # Mock rg output
                rg_result = MagicMock()
                rg_result.returncode = 0
                rg_result.stdout = "file.py:10:5:def main():\n"

                # Mock sk output
                sk_result = MagicMock()
                sk_result.returncode = 0
                sk_result.stdout = "file.py:10:5:def main():\n"
                sk_result.stderr = ""

                mock_run.side_effect = [rg_result, sk_result]

                with patch('skim_mcp_server.server.check_sk_installed', return_value=True):
                    result = fuzzy_search_content(directory=".", query="main")

                    assert result['success'] is True
                    assert len(result['selections']) == 1

    def test_fuzzy_search_content_no_matches(self):
        """Test content search with no matches."""
        with patch('shutil.which', return_value='/usr/bin/rg'):
            with patch('subprocess.run') as mock_run:
                rg_result = MagicMock()
                rg_result.returncode = 1
                rg_result.stdout = ""

                mock_run.return_value = rg_result

                with patch('skim_mcp_server.server.check_sk_installed', return_value=True):
                    result = fuzzy_search_content(directory=".", query="nonexistent")

                    assert result['success'] is False
                    assert 'No matches found' in result['error']


class TestFuzzyFilterLines:
    """Test fuzzy_filter_lines tool."""

    def test_fuzzy_filter_lines_success(self):
        """Test successful line filtering."""
        input_text = "apple\nbanana\ncherry\napricot"

        with patch('skim_mcp_server.server.check_sk_installed', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "apple\napricot\n"
                mock_result.stderr = ""

                mock_run.return_value = mock_result

                result = fuzzy_filter_lines(input_text=input_text, query="ap")

                assert result['success'] is True
                assert len(result['selections']) == 2

    def test_fuzzy_filter_lines_empty_input(self):
        """Test filtering with empty input."""
        result = fuzzy_filter_lines(input_text="", query="test")

        assert result['success'] is False
        assert 'No input text provided' in result['error']

    def test_fuzzy_filter_lines_with_delimiter(self):
        """Test filtering with field delimiter."""
        input_text = "name:john:30\nname:jane:25\nuser:bob:40"

        with patch('skim_mcp_server.server.check_sk_installed', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "name:john:30\nname:jane:25\n"
                mock_result.stderr = ""

                mock_run.return_value = mock_result

                result = fuzzy_filter_lines(
                    input_text=input_text,
                    query="name",
                    delimiter=":",
                    nth="1"
                )

                assert result['success'] is True


class TestFuzzySelectGitFiles:
    """Test fuzzy_select_git_files tool."""

    def test_fuzzy_select_git_files_success(self):
        """Test Git file selection."""
        with patch('shutil.which') as mock_which:
            mock_which.side_effect = lambda x: f'/usr/bin/{x}' if x in ['git', 'bat'] else None

            with patch('subprocess.run') as mock_run:
                # Mock git ls-files output
                git_result = MagicMock()
                git_result.returncode = 0
                git_result.stdout = "src/main.py\nsrc/utils.py\n"

                # Mock sk output
                sk_result = MagicMock()
                sk_result.returncode = 0
                sk_result.stdout = "src/main.py\n"
                sk_result.stderr = ""

                mock_run.side_effect = [git_result, sk_result]

                with patch('skim_mcp_server.server.check_sk_installed', return_value=True):
                    result = fuzzy_select_git_files(query="main")

                    assert result['success'] is True
                    assert len(result['selections']) == 1

    def test_fuzzy_select_git_files_not_git_repo(self):
        """Test Git file selection outside Git repository."""
        with patch('shutil.which', return_value='/usr/bin/git'):
            with patch('subprocess.run') as mock_run:
                git_result = MagicMock()
                git_result.returncode = 128  # Not a git repository
                git_result.stdout = ""

                mock_run.return_value = git_result

                with patch('skim_mcp_server.server.check_sk_installed', return_value=True):
                    result = fuzzy_select_git_files()

                    assert result['success'] is False
                    assert 'Not a git repository' in result['error']

    def test_fuzzy_select_git_files_no_git(self):
        """Test Git file selection when git is not installed."""
        with patch('shutil.which', return_value=None):
            result = fuzzy_select_git_files()

            assert result['success'] is False
            assert 'not installed' in result['error']


class TestInteractiveSearch:
    """Test interactive_search tool."""

    def test_interactive_search_success(self):
        """Test successful interactive search."""
        with patch('skim_mcp_server.server.check_sk_installed', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "result1\nresult2\n"
                mock_result.stderr = ""

                mock_run.return_value = mock_result

                result = interactive_search(
                    command="echo '{}'",
                    query="test"
                )

                assert result['success'] is True
                assert len(result['selections']) == 2

                # Verify interactive mode flags
                call_args = mock_run.call_args[0][0]
                assert '-i' in call_args
                assert '-c' in call_args

    def test_interactive_search_not_installed(self):
        """Test interactive search when sk is not installed."""
        with patch('skim_mcp_server.server.check_sk_installed', return_value=False):
            result = interactive_search(command="echo '{}'")

            assert result['success'] is False
            assert 'not installed' in result['error']


class TestIntegration:
    """Integration tests using actual filesystem."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace with test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_files = [
                "test1.py",
                "test2.py",
                "readme.md",
                "config.json",
            ]

            for filename in test_files:
                filepath = Path(tmpdir) / filename
                filepath.write_text(f"Content of {filename}\n")

            yield tmpdir

    def test_fuzzy_find_files_integration(self, temp_workspace):
        """Integration test for fuzzy_find_files (requires sk)."""
        if not check_sk_installed():
            pytest.skip("sk not installed")

        # This test would require actual user interaction with sk
        # For automated testing, we mock the sk response
        with patch('subprocess.run') as mock_run:
            # Mock find/fd output
            find_result = MagicMock()
            find_result.returncode = 0
            find_result.stdout = "\n".join([
                f"{temp_workspace}/test1.py",
                f"{temp_workspace}/test2.py",
            ])

            # Mock sk selection
            sk_result = MagicMock()
            sk_result.returncode = 0
            sk_result.stdout = f"{temp_workspace}/test1.py\n"
            sk_result.stderr = ""

            mock_run.side_effect = [find_result, sk_result]

            result = fuzzy_find_files(
                directory=temp_workspace,
                query="test1",
                preview=False
            )

            assert result['success'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])