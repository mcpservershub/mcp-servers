"""Tests for MCP server tools."""

import asyncio
import json
import tempfile
from pathlib import Path

import pytest
from selenium_mcp.server import (
    start_browser, close_session, list_sessions, switch_session,
    navigate, get_current_url, get_page_title, go_back, go_forward, refresh_page,
    find_element, find_elements, click_element, send_keys, get_element_text,
    get_element_attribute, get_element_property, is_element_displayed, is_element_enabled,
    get_element_info, hover, double_click, right_click, drag_and_drop,
    press_key, upload_file, take_screenshot, select_from_dropdown, handle_alert,
    switch_to_iframe, execute_script, open_new_tab, switch_to_tab, get_window_handles,
    set_cookie, get_cookies, clear_cookies, set_local_storage, get_local_storage,
    scroll_page, wait_for_condition, get_page_source, get_console_logs
)
from selenium_mcp.server import browser_manager


@pytest.mark.asyncio
class TestBrowserManagementTools:
    """Test browser management tools."""

    async def test_start_browser(self):
        """Test starting a browser."""
        result = await start_browser("chrome", {"headless": True})
        assert "Browser started with session ID:" in result
        assert "chrome_" in result

    async def test_start_browser_with_options(self):
        """Test starting a browser with custom options."""
        options = {
            "headless": True,
            "window_size": [1280, 720],
            "arguments": ["--disable-web-security"]
        }
        result = await start_browser("chrome", options)
        assert "Browser started with session ID:" in result

    async def test_list_sessions_empty(self):
        """Test listing sessions when none exist."""
        # Clean up any existing sessions
        await browser_manager.close_all_sessions()
        result = await list_sessions()
        sessions = json.loads(result)
        assert len(sessions) == 0

    async def test_list_sessions_with_sessions(self):
        """Test listing sessions with active sessions."""
        # Start a browser session
        await start_browser("chrome", {"headless": True})

        result = await list_sessions()
        sessions = json.loads(result)
        assert len(sessions) == 1
        assert sessions[0]["browser"] == "chrome"
        assert sessions[0]["is_current"] is True

    async def test_switch_session(self):
        """Test switching between sessions."""
        # Start two sessions
        result1 = await start_browser("chrome", {"headless": True})
        session_id1 = result1.split(": ")[1]

        result2 = await start_browser("chrome", {"headless": True})
        session_id2 = result2.split(": ")[1]

        # Switch to second session
        result = await switch_session(session_id2)
        assert f"Switched to session: {session_id2}" == result

        # Verify current session
        sessions_result = await list_sessions()
        sessions = json.loads(sessions_result)
        current_sessions = [s for s in sessions if s["is_current"]]
        assert len(current_sessions) == 1
        assert current_sessions[0]["session_id"] == session_id2

    async def test_close_session(self):
        """Test closing a session."""
        # Start a session
        result = await start_browser("chrome", {"headless": True})
        session_id = result.split(": ")[1]

        # Close the session
        close_result = await close_session(session_id)
        assert f"Closed browser session: {session_id}" == close_result

        # Verify session is closed
        sessions_result = await list_sessions()
        sessions = json.loads(sessions_result)
        assert len(sessions) == 0


@pytest.mark.asyncio
class TestNavigationTools:
    """Test navigation tools."""

    async def setup_method(self):
        """Set up a browser session for each test."""
        await start_browser("chrome", {"headless": True})

    async def teardown_method(self):
        """Clean up after each test."""
        await browser_manager.close_all_sessions()

    async def test_navigate(self):
        """Test navigation to URL."""
        test_url = "data:text/html,<h1>Test Page</h1><title>Test Title</title>"
        result = await navigate(test_url)
        assert f"Navigated to {test_url}" == result

    async def test_get_current_url(self):
        """Test getting current URL."""
        test_url = "data:text/html,<h1>Test Page</h1>"
        await navigate(test_url)
        current_url = await get_current_url()
        assert current_url == test_url

    async def test_get_page_title(self):
        """Test getting page title."""
        test_url = "data:text/html,<title>Test Title</title><h1>Test Page</h1>"
        await navigate(test_url)
        title = await get_page_title()
        assert title == "Test Title"

    async def test_refresh_page(self):
        """Test page refresh."""
        test_url = "data:text/html,<h1>Test Page</h1>"
        await navigate(test_url)
        result = await refresh_page()
        assert result == "Page refreshed"

    async def test_navigation_history(self):
        """Test back and forward navigation."""
        # Navigate to first page
        url1 = "data:text/html,<h1>Page 1</h1>"
        await navigate(url1)

        # Navigate to second page
        url2 = "data:text/html,<h1>Page 2</h1>"
        await navigate(url2)

        # Go back
        result = await go_back()
        assert result == "Navigated back"

        # Go forward
        result = await go_forward()
        assert result == "Navigated forward"


@pytest.mark.asyncio
class TestElementInteractionTools:
    """Test element interaction tools."""

    async def setup_method(self):
        """Set up browser session and test page."""
        await start_browser("chrome", {"headless": True})
        test_html = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <h1 id="main-title">Test Page</h1>
            <input type="text" id="text-input" name="username" placeholder="Enter text">
            <button id="test-button" onclick="this.innerHTML='Clicked!'">Click Me</button>
            <select id="dropdown">
                <option value="">Select</option>
                <option value="opt1">Option 1</option>
                <option value="opt2">Option 2</option>
            </select>
            <div class="test-item">Item 1</div>
            <div class="test-item">Item 2</div>
            <div class="test-item">Item 3</div>
            <div id="hover-target" onmouseover="this.style.color='red'">Hover me</div>
            <div id="drag-source" draggable="true">Drag me</div>
            <div id="drop-target">Drop here</div>
        </body>
        </html>
        """
        import base64
        encoded_html = base64.b64encode(test_html.encode()).decode()
        test_url = f"data:text/html;base64,{encoded_html}"
        await navigate(test_url)

    async def teardown_method(self):
        """Clean up after each test."""
        await browser_manager.close_all_sessions()

    async def test_find_element(self):
        """Test finding a single element."""
        result = await find_element("id", "main-title")
        assert "Element found: h1" == result

    async def test_find_elements(self):
        """Test finding multiple elements."""
        result = await find_elements("class", "test-item")
        assert "Found 3 elements" == result

    async def test_click_element(self):
        """Test clicking an element."""
        result = await click_element("id", "test-button")
        assert result == "Element clicked"

    async def test_send_keys(self):
        """Test sending keys to an element."""
        test_text = "Hello, World!"
        result = await send_keys("id", "text-input", test_text)
        assert result == f"Sent keys: '{test_text}'"

        # Verify text was entered
        text_result = await get_element_text("id", "text-input")
        # Note: Input elements might not have visible text, check value attribute instead
        value = await get_element_attribute("id", "text-input", "value")
        assert value == test_text

    async def test_get_element_text(self):
        """Test getting element text."""
        result = await get_element_text("id", "main-title")
        assert "Test Page" in result

    async def test_get_element_attribute(self):
        """Test getting element attribute."""
        result = await get_element_attribute("id", "text-input", "placeholder")
        assert result == "Enter text"

    async def test_get_element_property(self):
        """Test getting element property."""
        result = await get_element_property("id", "text-input", "tagName")
        assert result.upper() == "INPUT"

    async def test_is_element_displayed(self):
        """Test checking if element is displayed."""
        result = await is_element_displayed("id", "main-title")
        assert result == "true"

    async def test_is_element_enabled(self):
        """Test checking if element is enabled."""
        result = await is_element_enabled("id", "test-button")
        assert result == "true"

    async def test_get_element_info(self):
        """Test getting comprehensive element information."""
        result = await get_element_info("id", "main-title")
        info = json.loads(result)

        assert info["tag_name"] == "h1"
        assert "Test Page" in info["text"]
        assert info["displayed"] is True
        assert info["enabled"] is True
        assert info["attributes"]["id"] == "main-title"

    async def test_hover(self):
        """Test hovering over an element."""
        result = await hover("id", "hover-target")
        assert result == "Hovered over element"

    async def test_double_click(self):
        """Test double clicking an element."""
        result = await double_click("id", "test-button")
        assert result == "Double clicked element"

    async def test_right_click(self):
        """Test right clicking an element."""
        result = await right_click("id", "test-button")
        assert result == "Right clicked element"

    async def test_drag_and_drop(self):
        """Test drag and drop operation."""
        result = await drag_and_drop("id", "drag-source", "id", "drop-target")
        assert result == "Drag and drop completed"


@pytest.mark.asyncio
class TestKeyboardAndFileTools:
    """Test keyboard and file operation tools."""

    async def setup_method(self):
        """Set up browser session."""
        await start_browser("chrome", {"headless": True})

    async def teardown_method(self):
        """Clean up after each test."""
        await browser_manager.close_all_sessions()

    async def test_press_key(self):
        """Test pressing a key."""
        result = await press_key("Enter")
        assert result == "Pressed key 'Enter'"

    async def test_press_key_with_modifiers(self):
        """Test pressing a key with modifiers."""
        result = await press_key("c", ["ctrl"])
        assert result == "Pressed key 'c' with ctrl"

    async def test_upload_file(self, temp_file: str):
        """Test file upload."""
        # Create test page with file input
        test_html = '<input type="file" id="file-input">'
        import base64
        encoded_html = base64.b64encode(test_html.encode()).decode()
        test_url = f"data:text/html;base64,{encoded_html}"
        await navigate(test_url)

        result = await upload_file("id", "file-input", temp_file)
        assert f"File uploaded: {temp_file}" == result

    async def test_upload_file_not_found(self):
        """Test file upload with non-existent file."""
        test_html = '<input type="file" id="file-input">'
        import base64
        encoded_html = base64.b64encode(test_html.encode()).decode()
        test_url = f"data:text/html;base64,{encoded_html}"
        await navigate(test_url)

        result = await upload_file("id", "file-input", "/nonexistent/file.txt")
        assert "File not found:" in result

    async def test_take_screenshot_base64(self):
        """Test taking screenshot as base64."""
        test_url = "data:text/html,<h1>Screenshot Test</h1>"
        await navigate(test_url)

        result = await take_screenshot()
        # Should return base64 data
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_take_screenshot_to_file(self, temp_dir: str):
        """Test taking screenshot to file."""
        test_url = "data:text/html,<h1>Screenshot Test</h1>"
        await navigate(test_url)

        output_path = str(Path(temp_dir) / "test_screenshot.png")
        result = await take_screenshot(output_path)
        assert f"Screenshot saved to: {output_path}" == result

        # Verify file exists
        assert Path(output_path).exists()
        assert Path(output_path).stat().st_size > 0


@pytest.mark.asyncio
class TestAdvancedWebTools:
    """Test advanced web interaction tools."""

    async def setup_method(self):
        """Set up browser session and test page."""
        await start_browser("chrome", {"headless": True})

    async def teardown_method(self):
        """Clean up after each test."""
        await browser_manager.close_all_sessions()

    async def test_select_from_dropdown(self):
        """Test selecting from dropdown."""
        test_html = """
        <select id="test-select">
            <option value="">Select</option>
            <option value="opt1">Option 1</option>
            <option value="opt2">Option 2</option>
        </select>
        """
        import base64
        encoded_html = base64.b64encode(test_html.encode()).decode()
        test_url = f"data:text/html;base64,{encoded_html}"
        await navigate(test_url)

        result = await select_from_dropdown("id", "test-select", option_text="Option 1")
        assert result == "Selected option by text: Option 1"

    async def test_execute_script(self):
        """Test executing JavaScript."""
        await navigate("data:text/html,<title>Script Test</title>")

        # Test simple script
        result = await execute_script("return document.title;")
        assert result == "Script Test"

        # Test script with arguments
        result = await execute_script("return arguments[0] + arguments[1];", [5, 3])
        assert result == "8"

    async def test_switch_to_iframe_and_back(self):
        """Test switching to iframe and back."""
        test_html = """
        <iframe id="test-frame" src="data:text/html,<h1>Iframe Content</h1>"></iframe>
        <h1>Main Content</h1>
        """
        import base64
        encoded_html = base64.b64encode(test_html.encode()).decode()
        test_url = f"data:text/html;base64,{encoded_html}"
        await navigate(test_url)

        # Switch to iframe
        result = await switch_to_iframe("id", "test-frame")
        assert "Switched to iframe by id: test-frame" == result

        # Switch back to main content
        result = await switch_to_iframe()
        assert result == "Switched to default content"

    async def test_handle_alert_no_alert(self):
        """Test handling alert when no alert is present."""
        await navigate("data:text/html,<h1>No Alert</h1>")
        result = await handle_alert("get_text")
        assert result == "No alert present"


@pytest.mark.asyncio
class TestWindowTabTools:
    """Test window and tab management tools."""

    async def setup_method(self):
        """Set up browser session."""
        await start_browser("chrome", {"headless": True})
        await navigate("data:text/html,<h1>Initial Tab</h1>")

    async def teardown_method(self):
        """Clean up after each test."""
        await browser_manager.close_all_sessions()

    async def test_get_window_handles(self):
        """Test getting window handles."""
        result = await get_window_handles()
        handles_info = json.loads(result)

        assert "handles" in handles_info
        assert "current" in handles_info
        assert "count" in handles_info
        assert handles_info["count"] >= 1

    async def test_open_new_tab(self):
        """Test opening a new tab."""
        result = await open_new_tab("data:text/html,<h1>New Tab</h1>")
        assert "Opened new tab and navigated to:" in result

    async def test_open_new_tab_without_url(self):
        """Test opening a new tab without URL."""
        result = await open_new_tab()
        assert "Opened new tab:" in result

    async def test_switch_to_tab(self):
        """Test switching to tab by index."""
        # Open a new tab
        await open_new_tab()

        # Switch back to first tab
        result = await switch_to_tab(0)
        assert result == "Switched to tab 0"

    async def test_switch_to_invalid_tab(self):
        """Test switching to invalid tab index."""
        result = await switch_to_tab(99)
        assert "Tab index 99 out of range" in result


@pytest.mark.asyncio
class TestDataManagementTools:
    """Test data management tools."""

    async def setup_method(self):
        """Set up browser session."""
        await start_browser("chrome", {"headless": True})
        await navigate("data:text/html,<h1>Data Management Test</h1>")

    async def teardown_method(self):
        """Clean up after each test."""
        await browser_manager.close_all_sessions()

    async def test_cookie_operations(self):
        """Test cookie operations."""
        # Set cookie
        result = await set_cookie("test_cookie", "test_value")
        assert result == "Set cookie: test_cookie"

        # Get cookies
        result = await get_cookies()
        cookies = json.loads(result)
        cookie_names = [cookie["name"] for cookie in cookies]
        assert "test_cookie" in cookie_names

        # Clear cookies
        result = await clear_cookies()
        assert result == "Cleared all cookies"

    async def test_local_storage_operations(self):
        """Test local storage operations."""
        # Set local storage item
        result = await set_local_storage("test_key", "test_value")
        assert result == "Set local storage: test_key"

        # Get specific item
        result = await get_local_storage("test_key")
        assert result == "test_value"

        # Get all items
        result = await get_local_storage()
        storage_data = json.loads(result)
        assert "test_key" in storage_data
        assert storage_data["test_key"] == "test_value"

    async def test_scroll_page(self):
        """Test page scrolling."""
        # Create a tall page for scrolling
        tall_html = "<div style='height:2000px;'>Tall content</div>"
        import base64
        encoded_html = base64.b64encode(tall_html.encode()).decode()
        test_url = f"data:text/html;base64,{encoded_html}"
        await navigate(test_url)

        # Scroll down
        result = await scroll_page("down", 500)
        assert result == "Scrolled down by 500 pixels"

        # Scroll up
        result = await scroll_page("up", 200)
        assert result == "Scrolled up by 200 pixels"


@pytest.mark.asyncio
class TestPageAnalysisTools:
    """Test page analysis tools."""

    async def setup_method(self):
        """Set up browser session with test content."""
        await start_browser("chrome", {"headless": True})
        test_html = """
        <html>
        <head><title>Analysis Test</title></head>
        <body>
            <h1>Page Analysis Test</h1>
            <script>
                console.log('Test log message');
                console.warn('Test warning');
            </script>
        </body>
        </html>
        """
        import base64
        encoded_html = base64.b64encode(test_html.encode()).decode()
        test_url = f"data:text/html;base64,{encoded_html}"
        await navigate(test_url)

    async def teardown_method(self):
        """Clean up after each test."""
        await browser_manager.close_all_sessions()

    async def test_get_page_source(self):
        """Test getting page source."""
        result = await get_page_source()
        assert "Page Analysis Test" in result
        assert "<html>" in result

    async def test_get_console_logs(self):
        """Test getting console logs."""
        # Note: Console logs might not be available in all WebDriver configurations
        result = await get_console_logs()
        # Should either return logs or indicate they're not available
        assert isinstance(result, str)

    async def test_wait_for_condition_element_present(self):
        """Test waiting for element to be present."""
        result = await wait_for_condition("element_present", 5.0, "tag", "h1")
        assert "Element present: tag=h1" == result

    async def test_wait_for_condition_title_contains(self):
        """Test waiting for title to contain text."""
        result = await wait_for_condition("title_contains", 5.0, text="Analysis")
        assert "Title contains: Analysis" == result

    async def test_wait_for_condition_timeout(self):
        """Test wait condition timeout."""
        result = await wait_for_condition("element_present", 1.0, "id", "nonexistent")
        assert "Timeout waiting for condition: element_present" == result


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling in tools."""

    async def setup_method(self):
        """Set up browser session."""
        await start_browser("chrome", {"headless": True})

    async def teardown_method(self):
        """Clean up after each test."""
        await browser_manager.close_all_sessions()

    async def test_element_not_found_error(self):
        """Test handling of element not found errors."""
        await navigate("data:text/html,<h1>Test</h1>")
        result = await click_element("id", "nonexistent-element", 1.0)
        assert "Timeout error:" in result or "Element not found:" in result

    async def test_invalid_url_navigation(self):
        """Test navigation with invalid URL."""
        result = await navigate("not-a-valid-url")
        assert "Error:" in result

    async def test_no_session_error(self):
        """Test operations when no session exists."""
        # Close all sessions
        await browser_manager.close_all_sessions()

        result = await navigate("http://example.com")
        assert "Error:" in result and "No active browser session" in result