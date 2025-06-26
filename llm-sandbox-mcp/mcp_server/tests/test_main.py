

import unittest
from unittest.mock import MagicMock, patch

from mcp_server.main import start_sandbox, list_sandboxes, stop_sandbox


class TestMCPServer(unittest.TestCase):

    @patch('llm_sandbox.SandboxSession')
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
        mock_sandbox_session.assert_called_once_with(
            backend="docker",
            dockerfile=None,
            image='python:3.9-slim',
            lang='python',
            keep_template=False
        )
        mock_session_instance.run.assert_called_once_with("print('Hello, World!')")

    @patch('llm_sandbox.SandboxSession')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('os.remove', new_callable=MagicMock)
    def test_start_sandbox_with_output_file(self, mock_os_remove, mock_open, mock_sandbox_session):
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
        mock_sandbox_session.assert_called_once_with(
            backend="docker",
            dockerfile=None,
            image='python:3.9-slim',
            lang='python',
            keep_template=False
        )
        mock_session_instance.run.assert_called_once_with("print('Hello')")

    @patch('llm_sandbox.SandboxSession', side_effect=Exception("Sandbox error"))
    def test_start_sandbox_error_handling(self, mock_sandbox_session):
        # Act
        result = start_sandbox(sandbox_source="python:3.9-slim", code="invalid code")

        # Assert
        self.assertEqual(result["status"], "Failed to start or execute in sandbox.")
        self.assertIn("Sandbox error", result["error"])

    def test_list_sandboxes(self):
        # Act
        result = list_sandboxes()

        # Assert
        self.assertEqual(result["status"], "Not implemented yet. Placeholder for listing sandboxes.")

    def test_stop_sandbox(self):
        # Arrange
        session_id = "test_session_id"

        # Act
        result = stop_sandbox(session_id)

        # Assert
        self.assertEqual(result["status"], f"Not implemented yet. Placeholder for stopping sandbox session {session_id}.")

if __name__ == '__main__':
    unittest.main()
