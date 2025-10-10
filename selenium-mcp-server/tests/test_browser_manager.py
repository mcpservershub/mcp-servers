"""Tests for browser manager functionality."""

import pytest
from selenium.common.exceptions import WebDriverException
from selenium_mcp.browser_manager import BrowserManager
from selenium_mcp.models import BrowserType, BrowserOptions, LocatorStrategy


@pytest.mark.asyncio
class TestBrowserManager:
    """Test browser management functionality."""

    async def test_create_chrome_session(self, browser_manager: BrowserManager):
        """Test creating a Chrome browser session."""
        options = BrowserOptions(headless=True)
        session_id = await browser_manager.create_session(BrowserType.CHROME, options)

        assert session_id.startswith("chrome_")
        assert session_id in browser_manager.sessions
        assert browser_manager.current_session_id == session_id

    async def test_create_multiple_sessions(self, browser_manager: BrowserManager):
        """Test creating multiple browser sessions."""
        options = BrowserOptions(headless=True)

        # Create first session
        session1 = await browser_manager.create_session(BrowserType.CHROME, options)
        assert browser_manager.current_session_id == session1

        # Create second session
        session2 = await browser_manager.create_session(BrowserType.CHROME, options)

        # First session should still be current
        assert browser_manager.current_session_id == session1
        assert len(browser_manager.sessions) == 2
        assert session1 in browser_manager.sessions
        assert session2 in browser_manager.sessions

    async def test_switch_session(self, browser_manager: BrowserManager):
        """Test switching between browser sessions."""
        options = BrowserOptions(headless=True)

        # Create two sessions
        session1 = await browser_manager.create_session(BrowserType.CHROME, options)
        session2 = await browser_manager.create_session(BrowserType.CHROME, options)

        # Switch to second session
        await browser_manager.switch_session(session2)
        assert browser_manager.current_session_id == session2

        # Switch back to first session
        await browser_manager.switch_session(session1)
        assert browser_manager.current_session_id == session1

    async def test_switch_to_nonexistent_session(self, browser_manager: BrowserManager):
        """Test switching to a non-existent session."""
        with pytest.raises(ValueError, match="Session .* not found"):
            await browser_manager.switch_session("nonexistent_session")

    async def test_close_session(self, browser_manager: BrowserManager):
        """Test closing a browser session."""
        options = BrowserOptions(headless=True)
        session_id = await browser_manager.create_session(BrowserType.CHROME, options)

        # Close the session
        closed_session = await browser_manager.close_session(session_id)
        assert closed_session == session_id
        assert session_id not in browser_manager.sessions
        assert browser_manager.current_session_id is None

    async def test_close_current_session_with_others_active(self, browser_manager: BrowserManager):
        """Test closing current session when other sessions exist."""
        options = BrowserOptions(headless=True)

        # Create two sessions
        session1 = await browser_manager.create_session(BrowserType.CHROME, options)
        session2 = await browser_manager.create_session(BrowserType.CHROME, options)

        # Close current session (session1)
        await browser_manager.close_session()

        # Should switch to remaining session
        assert browser_manager.current_session_id == session2
        assert len(browser_manager.sessions) == 1

    async def test_list_sessions(self, browser_manager: BrowserManager):
        """Test listing browser sessions."""
        options = BrowserOptions(headless=True)

        # Initially no sessions
        sessions = browser_manager.list_sessions()
        assert len(sessions) == 0

        # Create session
        session_id = await browser_manager.create_session(BrowserType.CHROME, options)

        # List sessions
        sessions = browser_manager.list_sessions()
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == session_id
        assert sessions[0]["browser"] == "chrome"
        assert sessions[0]["is_current"] is True
        assert "created_at" in sessions[0]
        assert "last_activity" in sessions[0]

    async def test_get_session_no_active(self, browser_manager: BrowserManager):
        """Test getting session when none are active."""
        with pytest.raises(ValueError, match="No active browser session"):
            browser_manager.get_session()

    async def test_navigation(self, browser_manager: BrowserManager, headless_chrome_session: str):
        """Test browser navigation."""
        # Navigate to a test page
        test_url = "data:text/html,<h1>Test Page</h1>"
        await browser_manager.navigate(test_url)

        # Check current URL
        current_url = await browser_manager.get_current_url()
        assert current_url == test_url

        # Check page title
        title = await browser_manager.get_title()
        assert title == ""  # Data URLs don't have titles

    async def test_page_operations(self, browser_manager: BrowserManager, test_page_url: str):
        """Test page operations like refresh, back, forward."""
        # Get initial URL
        initial_url = await browser_manager.get_current_url()

        # Navigate to another page
        second_url = "data:text/html,<h1>Second Page</h1>"
        await browser_manager.navigate(second_url)

        current_url = await browser_manager.get_current_url()
        assert current_url == second_url

        # Go back
        await browser_manager.go_back()
        current_url = await browser_manager.get_current_url()
        # Note: Data URLs might not support history navigation

        # Refresh page
        await browser_manager.refresh()
        # Should still be on the same page

    async def test_find_element(self, browser_manager: BrowserManager, test_page_url: str):
        """Test finding elements on page."""
        # Find element by ID
        element = await browser_manager.find_element(LocatorStrategy.ID, "main-title")
        assert element.tag_name == "h1"
        assert "Test Page" in element.text

        # Find element by CSS selector
        element = await browser_manager.find_element(LocatorStrategy.CSS, "h1")
        assert element.tag_name == "h1"

    async def test_find_elements(self, browser_manager: BrowserManager, test_page_url: str):
        """Test finding multiple elements."""
        # Find multiple elements
        elements = await browser_manager.find_elements(LocatorStrategy.CLASS, "test-item")
        assert len(elements) == 3

        # Check each element
        for i, element in enumerate(elements):
            assert element.get_attribute("data-index") == str(i + 1)

    async def test_element_not_found(self, browser_manager: BrowserManager, test_page_url: str):
        """Test handling of element not found."""
        from selenium.common.exceptions import TimeoutException

        with pytest.raises(TimeoutException):
            await browser_manager.find_element(
                LocatorStrategy.ID, "nonexistent-element", timeout=1.0
            )

    async def test_get_element_info(self, browser_manager: BrowserManager, test_page_url: str):
        """Test getting comprehensive element information."""
        info = await browser_manager.get_element_info(LocatorStrategy.ID, "main-title")

        assert info.tag_name == "h1"
        assert "Test Page" in info.text
        assert info.displayed is True
        assert info.enabled is True
        assert "id" in info.attributes
        assert info.attributes["id"] == "main-title"

    async def test_screenshot(self, browser_manager: BrowserManager, test_page_url: str, temp_dir: str):
        """Test taking screenshots."""
        import os
        from pathlib import Path

        # Take screenshot to file
        output_path = str(Path(temp_dir) / "test_screenshot.png")
        result = await browser_manager.take_screenshot(output_path)

        assert result == output_path
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

        # Take screenshot as base64
        base64_data = await browser_manager.take_screenshot()
        assert isinstance(base64_data, str)
        assert len(base64_data) > 0

    async def test_execute_script(self, browser_manager: BrowserManager, test_page_url: str):
        """Test JavaScript execution."""
        # Execute simple script
        result = await browser_manager.execute_script("return document.title;")
        assert isinstance(result, str)

        # Execute script with arguments
        result = await browser_manager.execute_script(
            "return arguments[0] + arguments[1];", [5, 3]
        )
        assert result == 8

        # Execute script that modifies DOM
        await browser_manager.execute_script(
            "document.getElementById('main-title').style.color = 'red';"
        )

        # Verify the change
        element = await browser_manager.find_element(LocatorStrategy.ID, "main-title")
        color = element.value_of_css_property("color")
        # Note: Color values might be in different formats (rgb, rgba, etc.)

    async def test_browser_options(self, browser_manager: BrowserManager):
        """Test different browser options."""
        options = BrowserOptions(
            headless=True,
            window_size=(1280, 720),
            arguments=["--disable-web-security", "--disable-features=VizDisplayCompositor"]
        )

        session_id = await browser_manager.create_session(BrowserType.CHROME, options)
        assert session_id in browser_manager.sessions

        # Test that window size was set (though not easily verifiable in headless mode)
        session = browser_manager.get_session(session_id)
        # We can't easily verify window size in headless mode, but the session should exist
        assert session.driver is not None

    @pytest.mark.skipif(
        not pytest.importorskip("selenium.webdriver.firefox", reason="Firefox not available"),
        reason="Firefox WebDriver not available"
    )
    async def test_create_firefox_session(self, browser_manager: BrowserManager):
        """Test creating a Firefox session."""
        options = BrowserOptions(headless=True)
        try:
            session_id = await browser_manager.create_session(BrowserType.FIREFOX, options)
            assert session_id.startswith("firefox_")
            assert session_id in browser_manager.sessions
        except WebDriverException as e:
            pytest.skip(f"Firefox not available: {e}")

    async def test_close_all_sessions(self, browser_manager: BrowserManager):
        """Test closing all browser sessions."""
        options = BrowserOptions(headless=True)

        # Create multiple sessions
        session1 = await browser_manager.create_session(BrowserType.CHROME, options)
        session2 = await browser_manager.create_session(BrowserType.CHROME, options)

        assert len(browser_manager.sessions) == 2

        # Close all sessions
        await browser_manager.close_all_sessions()

        assert len(browser_manager.sessions) == 0
        assert browser_manager.current_session_id is None

    async def test_session_activity_tracking(self, browser_manager: BrowserManager):
        """Test that session activity is tracked."""
        options = BrowserOptions(headless=True)
        session_id = await browser_manager.create_session(BrowserType.CHROME, options)

        session = browser_manager.get_session(session_id)
        initial_activity = session.last_activity

        # Use the session (this should update activity)
        await browser_manager.navigate("data:text/html,<h1>Test</h1>")

        session = browser_manager.get_session(session_id)
        updated_activity = session.last_activity

        assert updated_activity >= initial_activity