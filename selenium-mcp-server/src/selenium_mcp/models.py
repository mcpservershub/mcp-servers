"""Pydantic models for request/response validation."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class BrowserType(str, Enum):
    """Supported browser types."""
    CHROME = "chrome"
    FIREFOX = "firefox"
    EDGE = "edge"


class LocatorStrategy(str, Enum):
    """Element locator strategies."""
    ID = "id"
    CSS = "css"
    XPATH = "xpath"
    NAME = "name"
    TAG = "tag"
    CLASS = "class"


class BrowserOptions(BaseModel):
    """Browser configuration options."""
    headless: Optional[bool] = Field(default=False, description="Run browser in headless mode")
    arguments: Optional[List[str]] = Field(default_factory=list, description="Additional browser arguments")
    window_size: Optional[tuple[int, int]] = Field(default=None, description="Browser window size (width, height)")
    user_data_dir: Optional[str] = Field(default=None, description="User data directory path")
    proxy: Optional[str] = Field(default=None, description="Proxy server URL")


class StartBrowserRequest(BaseModel):
    """Request model for starting a browser."""
    browser: BrowserType = Field(description="Browser type to launch")
    options: Optional[BrowserOptions] = Field(default_factory=BrowserOptions, description="Browser options")


class NavigateRequest(BaseModel):
    """Request model for navigation."""
    url: str = Field(description="URL to navigate to")

    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://', 'file://', 'data:')):
            raise ValueError('URL must start with http://, https://, file://, or data:')
        return v


class ElementRequest(BaseModel):
    """Base request model for element operations."""
    by: LocatorStrategy = Field(description="Locator strategy")
    value: str = Field(description="Locator value")
    timeout: Optional[float] = Field(default=10.0, description="Timeout in seconds")

    @validator('timeout')
    def validate_timeout(cls, v):
        if v <= 0:
            raise ValueError('Timeout must be positive')
        return v


class SendKeysRequest(ElementRequest):
    """Request model for sending keys."""
    text: str = Field(description="Text to type")
    clear_first: Optional[bool] = Field(default=True, description="Clear field before typing")


class DragDropRequest(ElementRequest):
    """Request model for drag and drop."""
    target_by: LocatorStrategy = Field(description="Target element locator strategy")
    target_value: str = Field(description="Target element locator value")


class UploadFileRequest(ElementRequest):
    """Request model for file upload."""
    file_path: str = Field(description="Absolute path to file")

    @validator('file_path')
    def validate_file_path(cls, v):
        if not v.startswith('/'):
            raise ValueError('File path must be absolute')
        return v


class ScreenshotRequest(BaseModel):
    """Request model for screenshots."""
    output_path: Optional[str] = Field(default=None, description="Output file path")
    element_by: Optional[LocatorStrategy] = Field(default=None, description="Element locator strategy for element screenshot")
    element_value: Optional[str] = Field(default=None, description="Element locator value for element screenshot")
    full_page: Optional[bool] = Field(default=False, description="Capture full page screenshot")


class ScriptRequest(BaseModel):
    """Request model for JavaScript execution."""
    script: str = Field(description="JavaScript code to execute")
    args: Optional[List[Any]] = Field(default_factory=list, description="Script arguments")


class CookieRequest(BaseModel):
    """Request model for cookie operations."""
    name: str = Field(description="Cookie name")
    value: Optional[str] = Field(default=None, description="Cookie value")
    domain: Optional[str] = Field(default=None, description="Cookie domain")
    path: Optional[str] = Field(default="/", description="Cookie path")
    secure: Optional[bool] = Field(default=False, description="Secure cookie flag")
    http_only: Optional[bool] = Field(default=False, description="HttpOnly cookie flag")


class LocalStorageRequest(BaseModel):
    """Request model for local storage operations."""
    key: str = Field(description="Storage key")
    value: Optional[str] = Field(default=None, description="Storage value")


class WaitConditionRequest(BaseModel):
    """Request model for wait conditions."""
    condition: str = Field(description="Wait condition type")
    by: Optional[LocatorStrategy] = Field(default=None, description="Element locator strategy")
    value: Optional[str] = Field(default=None, description="Element locator value")
    timeout: Optional[float] = Field(default=10.0, description="Timeout in seconds")
    text: Optional[str] = Field(default=None, description="Text to wait for")


class ScrollRequest(BaseModel):
    """Request model for scrolling."""
    direction: Optional[str] = Field(default="down", description="Scroll direction")
    pixels: Optional[int] = Field(default=None, description="Pixels to scroll")
    by: Optional[LocatorStrategy] = Field(default=None, description="Element to scroll to")
    value: Optional[str] = Field(default=None, description="Element locator value")


class SelectRequest(ElementRequest):
    """Request model for dropdown selection."""
    option_text: Optional[str] = Field(default=None, description="Option text to select")
    option_value: Optional[str] = Field(default=None, description="Option value to select")
    option_index: Optional[int] = Field(default=None, description="Option index to select")


class KeyRequest(BaseModel):
    """Request model for key press."""
    key: str = Field(description="Key to press")
    modifiers: Optional[List[str]] = Field(default_factory=list, description="Modifier keys")


class SessionResponse(BaseModel):
    """Response model for session operations."""
    session_id: str = Field(description="Session identifier")
    browser: str = Field(description="Browser type")
    status: str = Field(description="Session status")


class ElementInfo(BaseModel):
    """Element information model."""
    tag_name: str = Field(description="Element tag name")
    text: str = Field(description="Element text")
    enabled: bool = Field(description="Element enabled status")
    displayed: bool = Field(description="Element display status")
    selected: bool = Field(description="Element selected status")
    location: Dict[str, int] = Field(description="Element location")
    size: Dict[str, int] = Field(description="Element size")
    attributes: Dict[str, str] = Field(description="Element attributes")


class PageInfo(BaseModel):
    """Page information model."""
    url: str = Field(description="Current URL")
    title: str = Field(description="Page title")
    source_length: int = Field(description="HTML source length")


class NetworkLog(BaseModel):
    """Network log entry model."""
    method: str = Field(description="HTTP method")
    url: str = Field(description="Request URL")
    status: int = Field(description="Response status")
    timestamp: float = Field(description="Request timestamp")


class ConsoleLog(BaseModel):
    """Console log entry model."""
    level: str = Field(description="Log level")
    message: str = Field(description="Log message")
    timestamp: float = Field(description="Log timestamp")