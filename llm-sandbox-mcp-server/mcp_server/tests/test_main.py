

import unittest
from unittest.mock import MagicMock, patch

from mcp_server.main import start_sandbox


class TestMCPServer(unittest.TestCase):

    @patch('mcp_server.main.SandboxSession')
    def test_start_sandbox_with_image_and_code(self, mock_sandbox_session):
        # Arrange
        mock_session_instance = MagicMock()
        mock_run_output = MagicMock()
        mock_run_output.text = "Hello, World!"
        mock_run_output.exit_code = 0
        mock_session_instance.run.return_value = mock_run_output
        mock_sandbox_session.return_value.__enter__.return_value = mock_session_instance

        # Act
        result = start_sandbox(sandbox_source="python:3.9-slim", code="print('Hello, World!')", keep_template=False)

        # Assert
        self.assertEqual(result, {"status": "Code executed successfully.", "output": "Hello, World!", "exit_code": 0})
        from llm_sandbox import SandboxBackend
        mock_sandbox_session.assert_called_once_with(
            backend=SandboxBackend.DOCKER,
            dockerfile=None,
            image='python:3.9-slim',
            lang='python',
            keep_template=False
        )
        mock_session_instance.run.assert_called_once_with("print('Hello, World!')")

    @patch('mcp_server.main.SandboxSession')
    @patch('builtins.open', new_callable=MagicMock)
    def test_start_sandbox_with_output_file(self, mock_open, mock_sandbox_session):
        # Arrange
        mock_session_instance = MagicMock()
        mock_run_output = MagicMock()
        mock_run_output.text = "File Content"
        mock_run_output.exit_code = 0
        mock_session_instance.run.return_value = mock_run_output
        mock_sandbox_session.return_value.__enter__.return_value = mock_session_instance
        
        output_file = "/tmp/test_output.txt"

        # Act
        result = start_sandbox(sandbox_source="python:3.9-slim", code="print('Hello')", output_file_path=output_file)

        # Assert
        self.assertEqual(result["status"], "Code executed successfully.")
        mock_open.assert_called_once_with(output_file, "w")
        mock_open.return_value.__enter__.return_value.write.assert_called_once_with("File Content")
        from llm_sandbox import SandboxBackend
        mock_sandbox_session.assert_called_once_with(
            backend=SandboxBackend.DOCKER,
            dockerfile=None,
            image='python:3.9-slim',
            lang='python',
            keep_template=False
        )
        mock_session_instance.run.assert_called_once_with("print('Hello')")

    @patch('mcp_server.main.SandboxSession', side_effect=Exception("Sandbox error"))
    def test_start_sandbox_error_handling(self, mock_sandbox_session):
        # Act
        result = start_sandbox(sandbox_source="python:3.9-slim", code="invalid code")

        # Assert
        self.assertEqual(result["status"], "Failed to start or execute in sandbox.")
        self.assertIn("Sandbox error", result["error"])


if __name__ == '__main__':
    unittest.main()
