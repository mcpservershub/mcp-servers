"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError
from selenium_mcp.models import (
    BrowserType, BrowserOptions, LocatorStrategy,
    StartBrowserRequest, NavigateRequest, ElementRequest,
    SendKeysRequest, DragDropRequest, UploadFileRequest,
    ScreenshotRequest, ScriptRequest, CookieRequest,
    LocalStorageRequest, WaitConditionRequest, ScrollRequest,
    SelectRequest, KeyRequest, SessionResponse, ElementInfo, PageInfo
)


class TestEnums:
    """Test enum definitions."""

    def test_browser_type_values(self):
        """Test BrowserType enum values."""
        assert BrowserType.CHROME == "chrome"
        assert BrowserType.FIREFOX == "firefox"
        assert BrowserType.EDGE == "edge"

    def test_locator_strategy_values(self):
        """Test LocatorStrategy enum values."""
        assert LocatorStrategy.ID == "id"
        assert LocatorStrategy.CSS == "css"
        assert LocatorStrategy.XPATH == "xpath"
        assert LocatorStrategy.NAME == "name"
        assert LocatorStrategy.TAG == "tag"
        assert LocatorStrategy.CLASS == "class"


class TestBrowserOptions:
    """Test BrowserOptions model."""

    def test_default_options(self):
        """Test default browser options."""
        options = BrowserOptions()
        assert options.headless is False
        assert options.arguments == []
        assert options.window_size is None
        assert options.user_data_dir is None
        assert options.proxy is None

    def test_custom_options(self):
        """Test custom browser options."""
        options = BrowserOptions(
            headless=True,
            arguments=["--no-sandbox", "--disable-dev-shm-usage"],
            window_size=(1920, 1080),
            user_data_dir="/tmp/chrome-data",
            proxy="http://proxy.example.com:8080"
        )
        assert options.headless is True
        assert options.arguments == ["--no-sandbox", "--disable-dev-shm-usage"]
        assert options.window_size == (1920, 1080)
        assert options.user_data_dir == "/tmp/chrome-data"
        assert options.proxy == "http://proxy.example.com:8080"


class TestStartBrowserRequest:
    """Test StartBrowserRequest model."""

    def test_valid_request(self):
        """Test valid browser start request."""
        request = StartBrowserRequest(
            browser=BrowserType.CHROME,
            options=BrowserOptions(headless=True)
        )
        assert request.browser == BrowserType.CHROME
        assert request.options.headless is True

    def test_default_options(self):
        """Test browser start request with default options."""
        request = StartBrowserRequest(browser=BrowserType.FIREFOX)
        assert request.browser == BrowserType.FIREFOX
        assert request.options.headless is False


class TestNavigateRequest:
    """Test NavigateRequest model."""

    def test_valid_http_url(self):
        """Test valid HTTP URL."""
        request = NavigateRequest(url="http://example.com")
        assert request.url == "http://example.com"

    def test_valid_https_url(self):
        """Test valid HTTPS URL."""
        request = NavigateRequest(url="https://example.com")
        assert request.url == "https://example.com"

    def test_valid_file_url(self):
        """Test valid file URL."""
        request = NavigateRequest(url="file:///path/to/file.html")
        assert request.url == "file:///path/to/file.html"

    def test_valid_data_url(self):
        """Test valid data URL."""
        request = NavigateRequest(url="data:text/html,<h1>Hello</h1>")
        assert request.url == "data:text/html,<h1>Hello</h1>"

    def test_invalid_url(self):
        """Test invalid URL."""
        with pytest.raises(ValidationError) as exc_info:
            NavigateRequest(url="not-a-valid-url")

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "URL must start with" in str(errors[0]["msg"])


class TestElementRequest:
    """Test ElementRequest model."""

    def test_valid_request(self):
        """Test valid element request."""
        request = ElementRequest(
            by=LocatorStrategy.ID,
            value="test-element",
            timeout=5.0
        )
        assert request.by == LocatorStrategy.ID
        assert request.value == "test-element"
        assert request.timeout == 5.0

    def test_default_timeout(self):
        """Test default timeout value."""
        request = ElementRequest(
            by=LocatorStrategy.CSS,
            value=".test-class"
        )
        assert request.timeout == 10.0

    def test_invalid_timeout(self):
        """Test invalid timeout value."""
        with pytest.raises(ValidationError) as exc_info:
            ElementRequest(
                by=LocatorStrategy.ID,
                value="test",
                timeout=-1.0
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "Timeout must be positive" in str(errors[0]["msg"])


class TestSendKeysRequest:
    """Test SendKeysRequest model."""

    def test_valid_request(self):
        """Test valid send keys request."""
        request = SendKeysRequest(
            by=LocatorStrategy.NAME,
            value="username",
            text="testuser",
            clear_first=False
        )
        assert request.by == LocatorStrategy.NAME
        assert request.value == "username"
        assert request.text == "testuser"
        assert request.clear_first is False

    def test_default_clear_first(self):
        """Test default clear_first value."""
        request = SendKeysRequest(
            by=LocatorStrategy.ID,
            value="input",
            text="test"
        )
        assert request.clear_first is True


class TestDragDropRequest:
    """Test DragDropRequest model."""

    def test_valid_request(self):
        """Test valid drag and drop request."""
        request = DragDropRequest(
            by=LocatorStrategy.ID,
            value="source",
            target_by=LocatorStrategy.ID,
            target_value="target"
        )
        assert request.by == LocatorStrategy.ID
        assert request.value == "source"
        assert request.target_by == LocatorStrategy.ID
        assert request.target_value == "target"


class TestUploadFileRequest:
    """Test UploadFileRequest model."""

    def test_valid_request(self):
        """Test valid file upload request."""
        request = UploadFileRequest(
            by=LocatorStrategy.ID,
            value="file-input",
            file_path="/absolute/path/to/file.txt"
        )
        assert request.by == LocatorStrategy.ID
        assert request.value == "file-input"
        assert request.file_path == "/absolute/path/to/file.txt"

    def test_invalid_file_path(self):
        """Test invalid file path (not absolute)."""
        with pytest.raises(ValidationError) as exc_info:
            UploadFileRequest(
                by=LocatorStrategy.ID,
                value="file-input",
                file_path="relative/path.txt"
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "File path must be absolute" in str(errors[0]["msg"])


class TestScreenshotRequest:
    """Test ScreenshotRequest model."""

    def test_valid_request(self):
        """Test valid screenshot request."""
        request = ScreenshotRequest(
            output_path="/tmp/screenshot.png",
            element_by=LocatorStrategy.ID,
            element_value="target-element",
            full_page=True
        )
        assert request.output_path == "/tmp/screenshot.png"
        assert request.element_by == LocatorStrategy.ID
        assert request.element_value == "target-element"
        assert request.full_page is True

    def test_default_values(self):
        """Test default values."""
        request = ScreenshotRequest()
        assert request.output_path is None
        assert request.element_by is None
        assert request.element_value is None
        assert request.full_page is False


class TestScriptRequest:
    """Test ScriptRequest model."""

    def test_valid_request(self):
        """Test valid script request."""
        request = ScriptRequest(
            script="return document.title;",
            args=["arg1", "arg2"]
        )
        assert request.script == "return document.title;"
        assert request.args == ["arg1", "arg2"]

    def test_default_args(self):
        """Test default args value."""
        request = ScriptRequest(script="console.log('test');")
        assert request.args == []


class TestCookieRequest:
    """Test CookieRequest model."""

    def test_valid_request(self):
        """Test valid cookie request."""
        request = CookieRequest(
            name="session_id",
            value="abc123",
            domain="example.com",
            path="/app",
            secure=True,
            http_only=True
        )
        assert request.name == "session_id"
        assert request.value == "abc123"
        assert request.domain == "example.com"
        assert request.path == "/app"
        assert request.secure is True
        assert request.http_only is True

    def test_default_values(self):
        """Test default values."""
        request = CookieRequest(name="test")
        assert request.name == "test"
        assert request.value is None
        assert request.domain is None
        assert request.path == "/"
        assert request.secure is False
        assert request.http_only is False


class TestLocalStorageRequest:
    """Test LocalStorageRequest model."""

    def test_valid_request(self):
        """Test valid local storage request."""
        request = LocalStorageRequest(
            key="user_preference",
            value="dark_mode"
        )
        assert request.key == "user_preference"
        assert request.value == "dark_mode"

    def test_default_value(self):
        """Test default value."""
        request = LocalStorageRequest(key="test_key")
        assert request.key == "test_key"
        assert request.value is None


class TestWaitConditionRequest:
    """Test WaitConditionRequest model."""

    def test_valid_request(self):
        """Test valid wait condition request."""
        request = WaitConditionRequest(
            condition="element_visible",
            by=LocatorStrategy.ID,
            value="loading-spinner",
            timeout=30.0,
            text="Loading complete"
        )
        assert request.condition == "element_visible"
        assert request.by == LocatorStrategy.ID
        assert request.value == "loading-spinner"
        assert request.timeout == 30.0
        assert request.text == "Loading complete"

    def test_default_values(self):
        """Test default values."""
        request = WaitConditionRequest(condition="page_loaded")
        assert request.condition == "page_loaded"
        assert request.by is None
        assert request.value is None
        assert request.timeout == 10.0
        assert request.text is None


class TestScrollRequest:
    """Test ScrollRequest model."""

    def test_valid_request(self):
        """Test valid scroll request."""
        request = ScrollRequest(
            direction="up",
            pixels=500,
            by=LocatorStrategy.ID,
            value="target-element"
        )
        assert request.direction == "up"
        assert request.pixels == 500
        assert request.by == LocatorStrategy.ID
        assert request.value == "target-element"

    def test_default_values(self):
        """Test default values."""
        request = ScrollRequest()
        assert request.direction == "down"
        assert request.pixels is None
        assert request.by is None
        assert request.value is None


class TestSelectRequest:
    """Test SelectRequest model."""

    def test_valid_request(self):
        """Test valid select request."""
        request = SelectRequest(
            by=LocatorStrategy.NAME,
            value="country",
            option_text="United States",
            option_value="us",
            option_index=0
        )
        assert request.by == LocatorStrategy.NAME
        assert request.value == "country"
        assert request.option_text == "United States"
        assert request.option_value == "us"
        assert request.option_index == 0

    def test_default_values(self):
        """Test default values."""
        request = SelectRequest(
            by=LocatorStrategy.ID,
            value="dropdown"
        )
        assert request.option_text is None
        assert request.option_value is None
        assert request.option_index is None


class TestKeyRequest:
    """Test KeyRequest model."""

    def test_valid_request(self):
        """Test valid key request."""
        request = KeyRequest(
            key="Enter",
            modifiers=["ctrl", "shift"]
        )
        assert request.key == "Enter"
        assert request.modifiers == ["ctrl", "shift"]

    def test_default_modifiers(self):
        """Test default modifiers."""
        request = KeyRequest(key="Tab")
        assert request.key == "Tab"
        assert request.modifiers == []


class TestResponseModels:
    """Test response models."""

    def test_session_response(self):
        """Test SessionResponse model."""
        response = SessionResponse(
            session_id="chrome_123456789",
            browser="chrome",
            status="active"
        )
        assert response.session_id == "chrome_123456789"
        assert response.browser == "chrome"
        assert response.status == "active"

    def test_element_info(self):
        """Test ElementInfo model."""
        info = ElementInfo(
            tag_name="input",
            text="",
            enabled=True,
            displayed=True,
            selected=False,
            location={"x": 100, "y": 200},
            size={"width": 150, "height": 30},
            attributes={"id": "test-input", "type": "text"}
        )
        assert info.tag_name == "input"
        assert info.text == ""
        assert info.enabled is True
        assert info.displayed is True
        assert info.selected is False
        assert info.location == {"x": 100, "y": 200}
        assert info.size == {"width": 150, "height": 30}
        assert info.attributes["id"] == "test-input"

    def test_page_info(self):
        """Test PageInfo model."""
        info = PageInfo(
            url="https://example.com",
            title="Example Page",
            source_length=1024
        )
        assert info.url == "https://example.com"
        assert info.title == "Example Page"
        assert info.source_length == 1024