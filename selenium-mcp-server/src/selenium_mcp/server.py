"""Selenium MCP Server implementation with FastMCP - Fixed version with proper argument display."""

import asyncio
import base64
import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from mcp.server.fastmcp import FastMCP
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert
from selenium.common.exceptions import (
    WebDriverException, TimeoutException, NoSuchElementException,
    ElementNotVisibleException, ElementNotInteractableException,
    UnexpectedAlertPresentException, NoAlertPresentException, NoSuchWindowException
)

from .browser_manager import BrowserManager
from .models import (
    BrowserType, BrowserOptions, LocatorStrategy, ElementRequest,
    StartBrowserRequest, NavigateRequest, SendKeysRequest, DragDropRequest,
    UploadFileRequest, ScreenshotRequest, ScriptRequest, CookieRequest,
    LocalStorageRequest, WaitConditionRequest, ScrollRequest, SelectRequest,
    KeyRequest, SessionResponse, ElementInfo, PageInfo
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP instance
app = FastMCP("Selenium MCP Server")

# Global browser manager
browser_manager = BrowserManager()


def validate_locator_strategy(by: str) -> LocatorStrategy:
    """Convert string locator to LocatorStrategy enum."""
    try:
        return LocatorStrategy(by.lower())
    except ValueError:
        raise ValueError(f"Unsupported locator strategy '{by}'. Supported: id, css, xpath, name, tag, class")


# === BROWSER MANAGEMENT TOOLS ===

@app.tool()
async def start_browser(
    browser: str,
    headless: bool = True,  # Default to headless for AI agents
    window_width: Optional[int] = 1920,  # Default size for consistency
    window_height: Optional[int] = 1080,
    user_data_dir: Optional[str] = None,
    proxy: Optional[str] = None,
    extra_arguments: Optional[List[str]] = None
) -> str:
    """Launch a browser session.

    Args:
        browser: Browser type (chrome, firefox, edge)
        headless: Run browser in headless mode
        window_width: Browser window width in pixels
        window_height: Browser window height in pixels
        user_data_dir: User data directory path
        proxy: Proxy server URL
        extra_arguments: Additional browser arguments

    Returns:
        Session ID of the created browser session
    """
    try:
        # Validate and convert browser string to enum
        try:
            browser_type = BrowserType(browser.lower())
        except ValueError:
            return f"Error: Unsupported browser '{browser}'. Supported: chrome, firefox, edge"

        # Build window_size tuple if width and height provided
        window_size = None
        if window_width and window_height:
            window_size = (window_width, window_height)

        browser_opts = BrowserOptions(
            headless=headless,
            window_size=window_size,
            user_data_dir=user_data_dir,
            proxy=proxy,
            arguments=extra_arguments or []
        )

        session_id = await browser_manager.create_session(browser_type, browser_opts)
        return f"Browser started with session ID: {session_id}"
    except Exception as e:
        return f"Error: {str(e)}"


@app.tool()
async def close_session(session_id: Optional[str] = None) -> str:
    """Close a browser session.

    Args:
        session_id: Session ID to close (optional, defaults to current session)

    Returns:
        Confirmation message
    """
    try:
        closed_session = await browser_manager.close_session(session_id)
        return f"Closed browser session: {closed_session}"
    except Exception as e:
        return f"Error: {str(e)}"


@app.tool()
async def list_sessions() -> str:
    """List all active browser sessions.

    Returns:
        JSON string of active sessions information
    """
    try:
        sessions = browser_manager.list_sessions()
        return json.dumps(sessions, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


@app.tool()
async def switch_session(session_id: str) -> str:
    """Switch to a different browser session.

    Args:
        session_id: Session ID to switch to

    Returns:
        Confirmation message
    """
    try:
        await browser_manager.switch_session(session_id)
        return f"Switched to session: {session_id}"
    except Exception as e:
        return f"Error: {str(e)}"


# === NAVIGATION TOOLS ===

@app.tool()
async def navigate(url: str) -> str:
    """Navigate to a URL.

    Args:
        url: URL to navigate to

    Returns:
        Confirmation message
    """
    try:
        request = NavigateRequest(url=url)
        await browser_manager.navigate(request.url)
        return f"Navigated to {url}"
    except Exception as e:
        return f"Error: {str(e)}"


@app.tool()
async def get_current_url() -> str:
    """Get the current page URL.

    Returns:
        Current URL
    """
    try:
        return await browser_manager.get_current_url()
    except Exception as e:
        return f"Error: {str(e)}"


@app.tool()
async def get_page_title() -> str:
    """Get the current page title.

    Returns:
        Page title
    """
    try:
        return await browser_manager.get_title()
    except Exception as e:
        return f"Error: {str(e)}"


@app.tool()
async def go_back() -> str:
    """Go back in browser history.

    Returns:
        Confirmation message
    """
    try:
        await browser_manager.go_back()
        return "Navigated back"
    except Exception as e:
        return f"Error: {str(e)}"


@app.tool()
async def go_forward() -> str:
    """Go forward in browser history.

    Returns:
        Confirmation message
    """
    try:
        await browser_manager.go_forward()
        return "Navigated forward"
    except Exception as e:
        return f"Error: {str(e)}"


@app.tool()
async def refresh_page() -> str:
    """Refresh the current page.

    Returns:
        Confirmation message
    """
    try:
        await browser_manager.refresh()
        return "Page refreshed"
    except Exception as e:
        return f"Error: {str(e)}"


# === ELEMENT INTERACTION TOOLS ===

@app.tool()
async def find_element(
    by: str,
    value: str,
    timeout: Optional[float] = 10.0
) -> str:
    """Find an element on the page.

    Args:
        by: Locator strategy (id, css, xpath, name, tag, class)
        value: Locator value
        timeout: Maximum time to wait in seconds

    Returns:
        Element found confirmation message
    """
    try:
        locator_strategy = validate_locator_strategy(by)
        element = await browser_manager.find_element(locator_strategy, value, timeout)
        return f"Element found: {element.tag_name}"
    except Exception as e:
        return f"Error: {str(e)}"


@app.tool()
async def find_elements(
    by: str,
    value: str,
    timeout: Optional[float] = 10.0
) -> str:
    """Find multiple elements on the page.

    Args:
        by: Locator strategy (id, css, xpath, name, tag, class)
        value: Locator value
        timeout: Maximum time to wait in seconds

    Returns:
        Count of elements found
    """
    try:
        elements = await browser_manager.find_elements(by, value, timeout)
        return f"Found {len(elements)} elements"
    except Exception as e:
        return f"Error: {str(e)}"


@app.tool()
async def click_element(
    by: str,
    value: str,
    timeout: Optional[float] = 10.0
) -> str:
    """Click an element.

    Args:
        by: Locator strategy (id, css, xpath, name, tag, class)
        value: Locator value
        timeout: Maximum time to wait in seconds

    Returns:
        Confirmation message
    """
    try:
        locator_strategy = validate_locator_strategy(by)
        element = await browser_manager.find_element(locator_strategy, value, timeout)
        element.click()
        return "Element clicked"
    except Exception as e:
        return f"Error: {str(e)}"


@app.tool()
async def send_keys(
    by: str,
    value: str,
    text: str,
    timeout: Optional[float] = 10.0,
    clear_first: Optional[bool] = True
) -> str:
    """Send keys to an element (typing).

    Args:
        by: Locator strategy (id, css, xpath, name, tag, class)
        value: Locator value
        text: Text to type
        timeout: Maximum time to wait in seconds
        clear_first: Clear field before typing

    Returns:
        Confirmation message
    """
    try:
        element = await browser_manager.find_element(by, value, timeout)
        if clear_first:
            element.clear()
        element.send_keys(text)
        return f"Sent keys: '{text}'"
    except Exception as e:
        return f"Error: {str(e)}"


@app.tool()
async def get_element_text(
    by: str,
    value: str,
    timeout: Optional[float] = 10.0
) -> str:
    """Get the text content of an element.

    Args:
        by: Locator strategy (id, css, xpath, name, tag, class)
        value: Locator value
        timeout: Maximum time to wait in seconds

    Returns:
        Element text content
    """
    try:
        element = await browser_manager.find_element(by, value, timeout)
        return element.text
    except Exception as e:
        return f"Error: {str(e)}"


@app.tool()
async def get_element_attribute(
    by: str,
    value: str,
    attribute: str,
    timeout: Optional[float] = 10.0
) -> str:
    """Get an element's attribute value.

    Args:
        by: Locator strategy (id, css, xpath, name, tag, class)
        value: Locator value
        attribute: Attribute name
        timeout: Maximum time to wait in seconds

    Returns:
        Attribute value or empty string if not found
    """
    try:
        element = await browser_manager.find_element(by, value, timeout)
        attr_value = element.get_attribute(attribute)
        return attr_value or ""
    except Exception as e:
        return f"Error: {str(e)}"


@app.tool()
async def take_screenshot(
    output_path: Optional[str] = None,
    element_by: Optional[str] = None,
    element_value: Optional[str] = None,
    full_page: Optional[bool] = False
) -> str:
    """Take a screenshot.

    Args:
        output_path: Optional file path to save screenshot
        element_by: Optional element locator strategy for element screenshot
        element_value: Optional element locator value for element screenshot
        full_page: Take full page screenshot

    Returns:
        Base64 screenshot data or file path confirmation
    """
    try:
        session = browser_manager.get_session()

        if element_by and element_value:
            # Element screenshot
            element = await browser_manager.find_element(element_by, element_value, 10.0)
            screenshot_data = element.screenshot_as_base64
        else:
            # Page screenshot
            screenshot_data = await browser_manager.take_screenshot(output_path, full_page)
            if output_path:
                return f"Screenshot saved to: {output_path}"

        if output_path:
            with open(output_path, 'wb') as f:
                f.write(base64.b64decode(screenshot_data))
            return f"Screenshot saved to: {output_path}"

        return screenshot_data
    except Exception as e:
        return f"Error: {str(e)}"


# === MOUSE ACTIONS ===

@app.tool()
async def hover(
    by: str,
    value: str,
    timeout: Optional[float] = 10.0
) -> str:
    """Hover over an element.

    Args:
        by: Locator strategy (id, css, xpath, name, tag, class)
        value: Locator value
        timeout: Maximum time to wait in seconds

    Returns:
        Confirmation message
    """
    try:
        session = browser_manager.get_session()
        element = await browser_manager.find_element(by, value, timeout)
        actions = ActionChains(session.driver)
        actions.move_to_element(element).perform()
        return "Hovered over element"
    except Exception as e:
        return f"Error: {str(e)}"


@app.tool()
async def click_element_at_position(
    by: str,
    value: str,
    x_offset: int = 0,
    y_offset: int = 0,
    timeout: Optional[float] = 10.0
) -> str:
    """Click an element at a specific position offset.

    Args:
        by: Locator strategy (id, css, xpath, name, tag, class)
        value: Locator value
        x_offset: X coordinate offset from element center
        y_offset: Y coordinate offset from element center
        timeout: Maximum time to wait in seconds

    Returns:
        Confirmation message
    """
    try:
        session = browser_manager.get_session()
        element = await browser_manager.find_element(by, value, timeout)
        actions = ActionChains(session.driver)
        actions.move_to_element_with_offset(element, x_offset, y_offset).click().perform()
        return f"Clicked element at offset ({x_offset}, {y_offset})"
    except Exception as e:
        return f"Error: {str(e)}"


# === KEYBOARD ACTIONS ===

@app.tool()
async def press_key(
    key: str,
    modifiers: Optional[List[str]] = None
) -> str:
    """Press a keyboard key, optionally with modifiers.

    Args:
        key: Key to press (e.g., 'Enter', 'Tab', 'a', etc.)
        modifiers: Optional modifier keys (e.g., ['ctrl', 'shift'])

    Returns:
        Confirmation message
    """
    try:
        session = browser_manager.get_session()
        actions = ActionChains(session.driver)

        # Handle modifiers
        modifier_keys = []
        if modifiers:
            modifier_map = {
                'ctrl': Keys.CONTROL, 'control': Keys.CONTROL,
                'alt': Keys.ALT, 'shift': Keys.SHIFT,
                'cmd': Keys.COMMAND, 'command': Keys.COMMAND,
            }
            for mod in modifiers:
                if mod.lower() in modifier_map:
                    modifier_keys.append(modifier_map[mod.lower()])
                    actions.key_down(modifier_map[mod.lower()])

        # Map common key names
        key_map = {
            'enter': Keys.ENTER, 'return': Keys.RETURN, 'tab': Keys.TAB,
            'space': Keys.SPACE, 'escape': Keys.ESCAPE, 'esc': Keys.ESCAPE,
            'backspace': Keys.BACKSPACE, 'delete': Keys.DELETE, 'del': Keys.DELETE,
            'up': Keys.ARROW_UP, 'down': Keys.ARROW_DOWN,
            'left': Keys.ARROW_LEFT, 'right': Keys.ARROW_RIGHT,
            'home': Keys.HOME, 'end': Keys.END,
            'pageup': Keys.PAGE_UP, 'pagedown': Keys.PAGE_DOWN,
        }

        key_to_press = key_map.get(key.lower(), key)
        actions.send_keys(key_to_press)

        # Release modifiers
        for mod_key in reversed(modifier_keys):
            actions.key_up(mod_key)

        actions.perform()

        modifier_text = f" with {', '.join(modifiers)}" if modifiers else ""
        return f"Pressed key '{key}'{modifier_text}"
    except Exception as e:
        return f"Error: {str(e)}"


# === ADVANCED WEB INTERACTIONS ===

@app.tool()
async def execute_script(
    script: str,
    args: Optional[List[Any]] = None
) -> str:
    """Execute JavaScript code.

    Args:
        script: JavaScript code to execute
        args: Optional arguments for the script

    Returns:
        Script result as string
    """
    try:
        result = await browser_manager.execute_script(script, args or [])
        return str(result) if result is not None else "null"
    except Exception as e:
        return f"Error: {str(e)}"


@app.tool()
async def set_cookie(
    name: str,
    value: str,
    domain: Optional[str] = None,
    path: Optional[str] = "/",
    secure: Optional[bool] = False,
    http_only: Optional[bool] = False
) -> str:
    """Set a cookie.

    Args:
        name: Cookie name
        value: Cookie value
        domain: Cookie domain
        path: Cookie path
        secure: Secure flag
        http_only: HttpOnly flag

    Returns:
        Confirmation message
    """
    try:
        session = browser_manager.get_session()

        cookie_dict = {
            'name': name, 'value': value, 'path': path,
            'secure': secure, 'httpOnly': http_only
        }

        if domain:
            cookie_dict['domain'] = domain

        session.driver.add_cookie(cookie_dict)
        return f"Set cookie: {name}"
    except Exception as e:
        return f"Error: {str(e)}"


@app.tool()
async def get_cookies() -> str:
    """Get all cookies.

    Returns:
        JSON string of all cookies
    """
    try:
        session = browser_manager.get_session()
        cookies = session.driver.get_cookies()
        return json.dumps(cookies, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


# Cleanup handler for graceful shutdown
async def cleanup():
    """Clean up all browser sessions on shutdown."""
    await browser_manager.close_all_sessions()


def main():
    """Main entry point."""
    import argparse
    import signal
    import sys

    parser = argparse.ArgumentParser(description="Selenium MCP Server")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level"
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(cleanup())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Run the FastMCP server
        app.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    finally:
        # Cleanup on exit
        asyncio.run(cleanup())


if __name__ == "__main__":
    main()