"""Browser session management."""

import asyncio
import logging
import os
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.alert import Alert
from selenium.common.exceptions import (
    WebDriverException, TimeoutException, NoSuchElementException,
    ElementNotVisibleException, ElementNotInteractableException,
    UnexpectedAlertPresentException, NoAlertPresentException
)
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from .models import BrowserType, BrowserOptions, LocatorStrategy, ElementInfo, PageInfo

logger = logging.getLogger(__name__)


class BrowserSession:
    """Manages a single browser session."""

    def __init__(self, session_id: str, browser: BrowserType, driver: webdriver.Remote):
        self.session_id = session_id
        self.browser = browser
        self.driver = driver
        self.created_at = time.time()
        self.last_activity = time.time()

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()

    async def close(self) -> None:
        """Close the browser session."""
        try:
            if self.driver:
                self.driver.quit()
                logger.info(f"Closed browser session {self.session_id}")
        except Exception as e:
            logger.error(f"Error closing session {self.session_id}: {e}")


class BrowserManager:
    """Manages multiple browser sessions."""

    def __init__(self):
        self.sessions: Dict[str, BrowserSession] = {}
        self.current_session_id: Optional[str] = None
        self._lock = asyncio.Lock()

    def _get_locator(self, by: LocatorStrategy, value: str) -> Tuple[str, str]:
        """Convert locator strategy to Selenium By."""
        locator_map = {
            LocatorStrategy.ID: By.ID,
            LocatorStrategy.CSS: By.CSS_SELECTOR,
            LocatorStrategy.XPATH: By.XPATH,
            LocatorStrategy.NAME: By.NAME,
            LocatorStrategy.TAG: By.TAG_NAME,
            LocatorStrategy.CLASS: By.CLASS_NAME,
        }
        return locator_map[by], value

    async def create_session(
        self,
        browser: BrowserType,
        options: BrowserOptions
    ) -> str:
        """Create a new browser session."""
        async with self._lock:
            session_id = f"{browser.value}_{int(time.time() * 1000)}"

            try:
                if browser == BrowserType.CHROME:
                    driver = await self._create_chrome_driver(options)
                elif browser == BrowserType.FIREFOX:
                    driver = await self._create_firefox_driver(options)
                elif browser == BrowserType.EDGE:
                    driver = await self._create_edge_driver(options)
                else:
                    raise ValueError(f"Unsupported browser: {browser}")

                session = BrowserSession(session_id, browser, driver)
                self.sessions[session_id] = session

                # Set as current session if it's the first one
                if not self.current_session_id:
                    self.current_session_id = session_id

                logger.info(f"Created {browser.value} session: {session_id}")
                return session_id

            except Exception as e:
                logger.error(f"Failed to create {browser.value} session: {e}")
                raise WebDriverException(f"Failed to create browser session: {str(e)}")

    async def _create_chrome_driver(self, options: BrowserOptions) -> webdriver.Remote:
        """Create Chrome WebDriver (Remote or Local)."""
        chrome_options = ChromeOptions()

        if options.headless:
            chrome_options.add_argument("--headless=new")
            # Additional headless optimizations
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-features=TranslateUI")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-component-extensions-with-background-pages")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--mute-audio")
            chrome_options.add_argument("--no-default-browser-check")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--disable-software-rasterizer")

        # Default arguments for stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")

        if options.arguments:
            for arg in options.arguments:
                chrome_options.add_argument(arg)

        if options.window_size:
            chrome_options.add_argument(f"--window-size={options.window_size[0]},{options.window_size[1]}")

        if options.user_data_dir:
            chrome_options.add_argument(f"--user-data-dir={options.user_data_dir}")

        if options.proxy:
            chrome_options.add_argument(f"--proxy-server={options.proxy}")

        # Check if we should use Selenium Grid (Remote WebDriver)
        selenium_grid_url = os.getenv('SELENIUM_GRID_URL')
        if selenium_grid_url:
            logger.info(f"Using Selenium Grid at: {selenium_grid_url}")
            return webdriver.Remote(
                command_executor=selenium_grid_url,
                options=chrome_options
            )
        else:
            # Use local WebDriver with webdriver-manager
            logger.info("Using local Chrome WebDriver")
            service = ChromeService(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=chrome_options)

    async def _create_firefox_driver(self, options: BrowserOptions) -> webdriver.Remote:
        """Create Firefox WebDriver (Remote or Local)."""
        firefox_options = FirefoxOptions()

        if options.headless:
            firefox_options.add_argument("--headless")
            # Firefox-specific headless optimizations
            firefox_options.set_preference("media.volume_scale", "0.0")  # Mute audio
            firefox_options.set_preference("dom.webnotifications.enabled", False)  # Disable notifications
            firefox_options.set_preference("geo.enabled", False)  # Disable geolocation
            firefox_options.set_preference("browser.cache.disk.enable", False)  # Disable disk cache
            firefox_options.set_preference("browser.cache.memory.enable", True)  # Use memory cache only

        if options.arguments:
            for arg in options.arguments:
                firefox_options.add_argument(arg)

        if options.window_size:
            firefox_options.add_argument(f"--width={options.window_size[0]}")
            firefox_options.add_argument(f"--height={options.window_size[1]}")

        # Check if we should use Selenium Grid (Remote WebDriver)
        selenium_grid_url = os.getenv('SELENIUM_GRID_URL')
        if selenium_grid_url:
            logger.info(f"Using Selenium Grid for Firefox at: {selenium_grid_url}")
            return webdriver.Remote(
                command_executor=selenium_grid_url,
                options=firefox_options
            )
        else:
            # Use local WebDriver with webdriver-manager
            logger.info("Using local Firefox WebDriver")
            service = FirefoxService(GeckoDriverManager().install())
            return webdriver.Firefox(service=service, options=firefox_options)

    async def _create_edge_driver(self, options: BrowserOptions) -> webdriver.Remote:
        """Create Edge WebDriver (Remote or Local)."""
        edge_options = EdgeOptions()

        if options.headless:
            edge_options.add_argument("--headless=new")

        # Default arguments for stability
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")

        if options.arguments:
            for arg in options.arguments:
                edge_options.add_argument(arg)

        if options.window_size:
            edge_options.add_argument(f"--window-size={options.window_size[0]},{options.window_size[1]}")

        # Check if we should use Selenium Grid (Remote WebDriver)
        selenium_grid_url = os.getenv('SELENIUM_GRID_URL')
        if selenium_grid_url:
            logger.info(f"Using Selenium Grid for Edge at: {selenium_grid_url}")
            return webdriver.Remote(
                command_executor=selenium_grid_url,
                options=edge_options
            )
        else:
            # Use local WebDriver with webdriver-manager
            logger.info("Using local Edge WebDriver")
            service = EdgeService(EdgeChromiumDriverManager().install())
            return webdriver.Edge(service=service, options=edge_options)

    def get_session(self, session_id: Optional[str] = None) -> BrowserSession:
        """Get a browser session."""
        if session_id is None:
            session_id = self.current_session_id

        if not session_id or session_id not in self.sessions:
            raise ValueError("No active browser session")

        session = self.sessions[session_id]
        session.update_activity()
        return session

    async def switch_session(self, session_id: str) -> str:
        """Switch to a different session."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        self.current_session_id = session_id
        return session_id

    async def close_session(self, session_id: Optional[str] = None) -> str:
        """Close a browser session."""
        if session_id is None:
            session_id = self.current_session_id

        if not session_id or session_id not in self.sessions:
            raise ValueError("No session to close")

        session = self.sessions[session_id]
        await session.close()

        del self.sessions[session_id]

        # Update current session if we closed it
        if session_id == self.current_session_id:
            self.current_session_id = next(iter(self.sessions.keys())) if self.sessions else None

        return session_id

    async def close_all_sessions(self) -> None:
        """Close all browser sessions."""
        for session in list(self.sessions.values()):
            await session.close()

        self.sessions.clear()
        self.current_session_id = None

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions."""
        return [
            {
                "session_id": session.session_id,
                "browser": session.browser.value,
                "created_at": session.created_at,
                "last_activity": session.last_activity,
                "is_current": session.session_id == self.current_session_id
            }
            for session in self.sessions.values()
        ]

    async def navigate(self, url: str, session_id: Optional[str] = None) -> None:
        """Navigate to URL."""
        session = self.get_session(session_id)
        session.driver.get(url)

    async def get_current_url(self, session_id: Optional[str] = None) -> str:
        """Get current URL."""
        session = self.get_session(session_id)
        return session.driver.current_url

    async def get_title(self, session_id: Optional[str] = None) -> str:
        """Get page title."""
        session = self.get_session(session_id)
        return session.driver.title

    async def get_page_source(self, session_id: Optional[str] = None) -> str:
        """Get page source."""
        session = self.get_session(session_id)
        return session.driver.page_source

    async def refresh(self, session_id: Optional[str] = None) -> None:
        """Refresh the page."""
        session = self.get_session(session_id)
        session.driver.refresh()

    async def go_back(self, session_id: Optional[str] = None) -> None:
        """Go back in browser history."""
        session = self.get_session(session_id)
        session.driver.back()

    async def go_forward(self, session_id: Optional[str] = None) -> None:
        """Go forward in browser history."""
        session = self.get_session(session_id)
        session.driver.forward()

    async def find_element(
        self,
        by: LocatorStrategy,
        value: str,
        timeout: float = 10.0,
        session_id: Optional[str] = None
    ) -> WebElement:
        """Find a single element."""
        session = self.get_session(session_id)
        locator_by, locator_value = self._get_locator(by, value)
        wait = WebDriverWait(session.driver, timeout)
        return wait.until(EC.presence_of_element_located((locator_by, locator_value)))

    async def find_elements(
        self,
        by: LocatorStrategy,
        value: str,
        timeout: float = 10.0,
        session_id: Optional[str] = None
    ) -> List[WebElement]:
        """Find multiple elements."""
        session = self.get_session(session_id)
        locator_by, locator_value = self._get_locator(by, value)
        wait = WebDriverWait(session.driver, timeout)
        wait.until(EC.presence_of_element_located((locator_by, locator_value)))
        return session.driver.find_elements(locator_by, locator_value)

    async def get_element_info(
        self,
        by: LocatorStrategy,
        value: str,
        timeout: float = 10.0,
        session_id: Optional[str] = None
    ) -> ElementInfo:
        """Get comprehensive element information."""
        element = await self.find_element(by, value, timeout, session_id)

        # Get all attributes
        attributes = {}
        try:
            # Common attributes to check
            common_attrs = ['id', 'class', 'name', 'type', 'value', 'href', 'src', 'alt', 'title']
            for attr in common_attrs:
                attr_value = element.get_attribute(attr)
                if attr_value is not None:
                    attributes[attr] = attr_value
        except Exception:
            pass

        return ElementInfo(
            tag_name=element.tag_name,
            text=element.text,
            enabled=element.is_enabled(),
            displayed=element.is_displayed(),
            selected=element.is_selected(),
            location=element.location,
            size=element.size,
            attributes=attributes
        )

    async def take_screenshot(
        self,
        output_path: Optional[str] = None,
        full_page: bool = False,
        session_id: Optional[str] = None
    ) -> str:
        """Take a screenshot."""
        session = self.get_session(session_id)

        if full_page:
            # Get full page dimensions
            total_height = session.driver.execute_script("return document.body.scrollHeight")
            viewport_height = session.driver.execute_script("return window.innerHeight")

            # Set window size to capture full page
            session.driver.set_window_size(1920, total_height)

        screenshot_data = session.driver.get_screenshot_as_base64()

        if output_path:
            import base64
            with open(output_path, 'wb') as f:
                f.write(base64.b64decode(screenshot_data))
            return output_path

        return screenshot_data

    async def execute_script(
        self,
        script: str,
        args: List[Any] = None,
        session_id: Optional[str] = None
    ) -> Any:
        """Execute JavaScript."""
        session = self.get_session(session_id)
        return session.driver.execute_script(script, args or [])