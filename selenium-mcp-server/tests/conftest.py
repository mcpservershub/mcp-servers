"""Test configuration and fixtures."""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from selenium_mcp.browser_manager import BrowserManager
from selenium_mcp.models import BrowserType, BrowserOptions


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def browser_manager() -> AsyncGenerator[BrowserManager, None]:
    """Create a browser manager instance for testing."""
    manager = BrowserManager()
    yield manager
    # Cleanup all sessions after test
    await manager.close_all_sessions()


@pytest.fixture
async def headless_chrome_session(browser_manager: BrowserManager) -> AsyncGenerator[str, None]:
    """Create a headless Chrome session for testing."""
    options = BrowserOptions(headless=True, arguments=["--no-sandbox", "--disable-dev-shm-usage"])
    session_id = await browser_manager.create_session(BrowserType.CHROME, options)
    yield session_id
    # Session will be cleaned up by browser_manager fixture


@pytest.fixture
def temp_file() -> Generator[str, None, None]:
    """Create a temporary file for testing file uploads."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Test file content\nLine 2\nLine 3")
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_path:
        yield temp_path


@pytest.fixture
def test_html_content() -> str:
    """Sample HTML content for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
        <style>
            .hidden { display: none; }
            .red { color: red; }
        </style>
    </head>
    <body>
        <h1 id="main-title">Test Page</h1>

        <form id="test-form" action="/submit" method="post">
            <input type="text" id="text-input" name="text" placeholder="Enter text">
            <input type="email" id="email-input" name="email" placeholder="Enter email">
            <input type="password" id="password-input" name="password" placeholder="Enter password">

            <select id="dropdown" name="choice">
                <option value="">Select an option</option>
                <option value="option1">Option 1</option>
                <option value="option2">Option 2</option>
                <option value="option3">Option 3</option>
            </select>

            <input type="checkbox" id="checkbox1" name="check1" value="yes">
            <label for="checkbox1">Checkbox 1</label>

            <input type="radio" id="radio1" name="radio" value="a">
            <label for="radio1">Radio A</label>
            <input type="radio" id="radio2" name="radio" value="b">
            <label for="radio2">Radio B</label>

            <input type="file" id="file-input" name="file">

            <button type="button" id="test-button" onclick="testClick()">Click Me</button>
            <button type="submit" id="submit-button">Submit</button>
        </form>

        <div id="click-result" class="hidden">Button was clicked!</div>

        <div id="hover-target" onmouseover="showHoverText()" onmouseout="hideHoverText()">
            Hover over me
        </div>
        <div id="hover-result" class="hidden">Hovered!</div>

        <div id="drag-source" draggable="true" style="width:50px;height:50px;background:blue;">
            Drag me
        </div>
        <div id="drop-target" style="width:100px;height:100px;border:2px dashed #ccc;">
            Drop here
        </div>

        <iframe id="test-iframe" src="data:text/html,<h1>Iframe Content</h1>"></iframe>

        <script>
            function testClick() {
                document.getElementById('click-result').classList.remove('hidden');
            }

            function showHoverText() {
                document.getElementById('hover-result').classList.remove('hidden');
            }

            function hideHoverText() {
                document.getElementById('hover-result').classList.add('hidden');
            }

            // Alert button
            function showAlert() {
                alert('Test alert message');
            }

            // Console logging for testing
            console.log('Page loaded');
            console.warn('Test warning');
            console.error('Test error');
        </script>

        <button onclick="showAlert()" id="alert-button">Show Alert</button>

        <!-- Multiple elements for testing find_elements -->
        <div class="test-item" data-index="1">Item 1</div>
        <div class="test-item" data-index="2">Item 2</div>
        <div class="test-item" data-index="3">Item 3</div>
    </body>
    </html>
    """


@pytest.fixture
async def test_page_url(browser_manager: BrowserManager, headless_chrome_session: str, test_html_content: str) -> str:
    """Create a test page with HTML content and return its data URL."""
    import base64

    # Create data URL from HTML content
    encoded_html = base64.b64encode(test_html_content.encode('utf-8')).decode('utf-8')
    data_url = f"data:text/html;base64,{encoded_html}"

    # Navigate to the test page
    await browser_manager.navigate(data_url, headless_chrome_session)

    return data_url


@pytest.mark.asyncio
async def pytest_configure():
    """Configure pytest for async tests."""
    pass