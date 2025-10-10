# Selenium MCP Server (Python)

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

A comprehensive **Model Context Protocol (MCP) server** for **Selenium WebDriver** automation, built in Python 3.12 using FastMCP. This server provides AI agents and applications with powerful browser automation capabilities through a standardized interface.

## 🚀 Features

### Core Browser Management
- **Multi-browser support**: Chrome, Firefox, Microsoft Edge
- **Session management**: Multiple concurrent browser sessions
- **Auto-driver management**: Automatic WebDriver installation and updates
- **Headless & headed modes**: Flexible browser configurations
- **Container-ready**: Optimized Docker support

### Comprehensive Element Interactions
- **Smart element finding**: Multiple locator strategies (ID, CSS, XPath, Name, Tag, Class)
- **Advanced interactions**: Click, type, hover, drag-and-drop, double-click, right-click
- **Element inspection**: Get text, attributes, properties, and comprehensive element info
- **State validation**: Check if elements are displayed, enabled, or selected

### Advanced Web Automation
- **Form handling**: Dropdown selection, file upload, form submission
- **JavaScript execution**: Run custom scripts with arguments
- **Alert handling**: Accept, dismiss, or interact with browser dialogs
- **Frame switching**: Navigate between iframes and main content
- **Window/tab management**: Open, close, and switch between tabs

### Enhanced Navigation & Interaction
- **Navigation controls**: Back, forward, refresh, URL navigation
- **Keyboard automation**: Key presses with modifier support
- **Mouse actions**: Precise cursor control and interactions
- **Scrolling**: Page and element scrolling capabilities
- **Screenshot capture**: Full page, element-specific, or viewport screenshots

### Data Management
- **Cookie operations**: Set, get, and clear cookies
- **Local storage**: Manage browser local storage
- **Session persistence**: Maintain state across operations
- **Wait conditions**: Smart waiting for various page states

### Developer Tools
- **Console logs**: Access browser console messages
- **Page analysis**: Get page source, title, and URL information
- **Network monitoring**: Basic network request tracking
- **Error handling**: Comprehensive error reporting and recovery

## 📦 Installation

### Using uv (Recommended)
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone <repository-url>
cd selenium-mcp-server

# Install dependencies
uv sync

# Run the server
uv run selenium-mcp
```

### Using pip
```bash
# Install from source
pip install -e .

# Or install development dependencies
pip install -e ".[dev]"
```

### Using Docker
```bash
# Build and run the container
docker-compose up selenium-mcp

# For development with hot reload
docker-compose up selenium-mcp-dev
```

## 🔧 Configuration

### MCP Client Configuration

#### Claude Desktop
Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "selenium": {
      "command": "uv",
      "args": ["run", "selenium-mcp"],
      "env": {
        "SELENIUM_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### Docker Configuration
```json
{
  "mcpServers": {
    "selenium-docker": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "selenium-mcp:latest"],
      "env": {
        "DISPLAY": ":99"
      }
    }
  }
}
```

#### Standalone Python
```json
{
  "mcpServers": {
    "selenium": {
      "command": "python",
      "args": ["-m", "selenium_mcp.server"],
      "cwd": "/path/to/selenium-mcp-server"
    }
  }
}
```

## 🛠️ Available Tools

### Browser Management

#### `start_browser`
Launch a new browser session.
```json
{
  "tool_name": "start_browser",
  "arguments": {
    "browser": "chrome",
    "options": {
      "headless": false,
      "window_size": [1920, 1080],
      "arguments": ["--disable-web-security"]
    }
  }
}
```

#### `close_session`
Close the current or specified browser session.
```json
{
  "tool_name": "close_session",
  "arguments": {
    "session_id": "chrome_1234567890"
  }
}
```

#### `list_sessions`
List all active browser sessions.
```json
{
  "tool_name": "list_sessions",
  "arguments": {}
}
```

#### `switch_session`
Switch to a different browser session.
```json
{
  "tool_name": "switch_session",
  "arguments": {
    "session_id": "firefox_1234567891"
  }
}
```

### Navigation

#### `navigate`
Navigate to a URL.
```json
{
  "tool_name": "navigate",
  "arguments": {
    "url": "https://example.com"
  }
}
```

#### `get_current_url`
Get the current page URL.
```json
{
  "tool_name": "get_current_url",
  "arguments": {}
}
```

#### `get_page_title`
Get the current page title.
```json
{
  "tool_name": "get_page_title",
  "arguments": {}
}
```

#### `go_back` / `go_forward` / `refresh_page`
Browser navigation controls.
```json
{
  "tool_name": "go_back",
  "arguments": {}
}
```

### Element Interaction

#### `find_element`
Find a single element on the page.
```json
{
  "tool_name": "find_element",
  "arguments": {
    "by": "id",
    "value": "search-input",
    "timeout": 10.0
  }
}
```

#### `find_elements`
Find multiple elements on the page.
```json
{
  "tool_name": "find_elements",
  "arguments": {
    "by": "css",
    "value": ".product-item",
    "timeout": 5.0
  }
}
```

#### `click_element`
Click an element.
```json
{
  "tool_name": "click_element",
  "arguments": {
    "by": "xpath",
    "value": "//button[@type='submit']",
    "timeout": 10.0
  }
}
```

#### `send_keys`
Type text into an element.
```json
{
  "tool_name": "send_keys",
  "arguments": {
    "by": "name",
    "value": "username",
    "text": "testuser",
    "timeout": 10.0,
    "clear_first": true
  }
}
```

#### `get_element_text`
Get element text content.
```json
{
  "tool_name": "get_element_text",
  "arguments": {
    "by": "class",
    "value": "error-message",
    "timeout": 5.0
  }
}
```

#### `get_element_info`
Get comprehensive element information.
```json
{
  "tool_name": "get_element_info",
  "arguments": {
    "by": "id",
    "value": "profile-form",
    "timeout": 10.0
  }
}
```

### Mouse Actions

#### `hover`
Hover over an element.
```json
{
  "tool_name": "hover",
  "arguments": {
    "by": "css",
    "value": ".dropdown-trigger",
    "timeout": 5.0
  }
}
```

#### `double_click` / `right_click`
Perform double-click or right-click on an element.
```json
{
  "tool_name": "double_click",
  "arguments": {
    "by": "id",
    "value": "editable-text",
    "timeout": 10.0
  }
}
```

#### `drag_and_drop`
Drag one element to another.
```json
{
  "tool_name": "drag_and_drop",
  "arguments": {
    "by": "id",
    "value": "draggable-item",
    "target_by": "id",
    "target_value": "drop-zone",
    "timeout": 10.0
  }
}
```

### Keyboard Actions

#### `press_key`
Press keyboard keys with optional modifiers.
```json
{
  "tool_name": "press_key",
  "arguments": {
    "key": "Enter",
    "modifiers": ["ctrl", "shift"]
  }
}
```

### File Operations

#### `upload_file`
Upload a file using a file input element.
```json
{
  "tool_name": "upload_file",
  "arguments": {
    "by": "id",
    "value": "file-input",
    "file_path": "/home/user/document.pdf",
    "timeout": 15.0
  }
}
```

#### `take_screenshot`
Capture screenshots.
```json
{
  "tool_name": "take_screenshot",
  "arguments": {
    "output_path": "/tmp/screenshot.png",
    "element_by": "id",
    "element_value": "main-content",
    "full_page": false
  }
}
```

### Advanced Interactions

#### `select_from_dropdown`
Select an option from a dropdown.
```json
{
  "tool_name": "select_from_dropdown",
  "arguments": {
    "by": "name",
    "value": "country",
    "option_text": "United States",
    "timeout": 10.0
  }
}
```

#### `handle_alert`
Handle JavaScript alerts.
```json
{
  "tool_name": "handle_alert",
  "arguments": {
    "action": "accept",
    "text": "Alert response text"
  }
}
```

#### `switch_to_iframe`
Switch to an iframe or back to main content.
```json
{
  "tool_name": "switch_to_iframe",
  "arguments": {
    "by": "id",
    "value": "payment-iframe"
  }
}
```

#### `execute_script`
Execute JavaScript code.
```json
{
  "tool_name": "execute_script",
  "arguments": {
    "script": "return document.title;",
    "args": []
  }
}
```

### Window/Tab Management

#### `open_new_tab`
Open a new browser tab.
```json
{
  "tool_name": "open_new_tab",
  "arguments": {
    "url": "https://example.com"
  }
}
```

#### `switch_to_tab`
Switch to a specific tab by index.
```json
{
  "tool_name": "switch_to_tab",
  "arguments": {
    "tab_index": 1
  }
}
```

#### `get_window_handles`
Get all window/tab handles.
```json
{
  "tool_name": "get_window_handles",
  "arguments": {}
}
```

### Data Management

#### `set_cookie` / `get_cookies` / `clear_cookies`
Cookie management operations.
```json
{
  "tool_name": "set_cookie",
  "arguments": {
    "name": "session_id",
    "value": "abc123",
    "domain": "example.com",
    "secure": true
  }
}
```

#### `set_local_storage` / `get_local_storage`
Local storage operations.
```json
{
  "tool_name": "set_local_storage",
  "arguments": {
    "key": "user_preference",
    "value": "dark_mode"
  }
}
```

### Page Analysis

#### `get_page_source`
Get the page HTML source.
```json
{
  "tool_name": "get_page_source",
  "arguments": {}
}
```

#### `get_console_logs`
Get browser console logs.
```json
{
  "tool_name": "get_console_logs",
  "arguments": {}
}
```

#### `scroll_page`
Scroll the page or to an element.
```json
{
  "tool_name": "scroll_page",
  "arguments": {
    "direction": "down",
    "pixels": 500
  }
}
```

#### `wait_for_condition`
Wait for specific conditions.
```json
{
  "tool_name": "wait_for_condition",
  "arguments": {
    "condition": "element_visible",
    "by": "id",
    "value": "loading-spinner",
    "timeout": 30.0
  }
}
```

## 🧪 Testing with MCP Inspector

The MCP Inspector is a powerful tool for testing MCP servers. Here's how to use it:

### Installation
```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Or use with npx
npx @modelcontextprotocol/inspector
```

### Running Tests
```bash
# Start the MCP Inspector with your server
mcp-inspector uv run selenium-mcp

# Or with specific environment variables
SELENIUM_LOG_LEVEL=DEBUG mcp-inspector python -m selenium_mcp.server
```

### Example Test Scenarios

#### Basic Browser Automation
1. **Start Browser Session**:
   - Tool: `start_browser`
   - Arguments: `{"browser": "chrome", "options": {"headless": false}}`

2. **Navigate to Website**:
   - Tool: `navigate`
   - Arguments: `{"url": "https://httpbin.org/forms/post"}`

3. **Fill Form Fields**:
   - Tool: `send_keys`
   - Arguments: `{"by": "name", "value": "custname", "text": "John Doe"}`

4. **Submit Form**:
   - Tool: `click_element`
   - Arguments: `{"by": "css", "value": "input[type=submit]"}`

#### Advanced Interactions
1. **Handle Dropdown Selection**:
   ```json
   {
     "tool": "select_from_dropdown",
     "arguments": {
       "by": "name",
       "value": "size",
       "option_text": "Medium"
     }
   }
   ```

2. **File Upload Test**:
   ```json
   {
     "tool": "upload_file",
     "arguments": {
       "by": "id",
       "value": "file",
       "file_path": "/tmp/test.txt"
     }
   }
   ```

3. **Screenshot Capture**:
   ```json
   {
     "tool": "take_screenshot",
     "arguments": {
       "output_path": "/tmp/test_screenshot.png",
       "full_page": true
     }
   }
   ```

## 🐳 Docker Usage

### Building the Image
```bash
# Build the image
docker build -t selenium-mcp .

# Or use docker-compose
docker-compose build
```

### Running the Container
```bash
# Run with docker-compose (recommended)
docker-compose up selenium-mcp

# Or run directly
docker run -it --rm \
  --shm-size=2g \
  --security-opt seccomp=unconfined \
  --cap-add=SYS_ADMIN \
  -v $(pwd)/screenshots:/home/selenium/screenshots \
  selenium-mcp
```

### Development Mode
```bash
# Run in development mode with hot reload
docker-compose up selenium-mcp-dev
```

### Environment Variables
- `SELENIUM_LOG_LEVEL`: Set log level (DEBUG, INFO, WARNING, ERROR)
- `DISPLAY`: X11 display for GUI mode (default: :99)
- `CHROME_BIN`: Chrome binary path
- `FIREFOX_BIN`: Firefox binary path

## 🔧 Development

### Setup Development Environment
```bash
# Clone the repository
git clone <repository-url>
cd selenium-mcp-server

# Install with development dependencies
uv sync --dev

# Install pre-commit hooks
uv run pre-commit install
```

### Code Quality Tools
```bash
# Format code
uv run black src/ tests/
uv run isort src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type checking
uv run mypy src/

# Run all quality checks
uv run pre-commit run --all-files
```

### Running Tests
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=selenium_mcp --cov-report=html

# Run specific test
uv run pytest tests/test_browser_manager.py -v
```

## 📋 Browser Requirements

### Chrome
- Automatically managed by `webdriver-manager`
- Supports headless and headed modes
- Best performance and stability

### Firefox
- Automatically managed by `webdriver-manager`
- Good compatibility with complex sites
- Supports most automation features

### Microsoft Edge
- Automatically managed by `webdriver-manager`
- Chromium-based, similar to Chrome
- Windows-optimized but works on Linux

## ⚠️ Troubleshooting

### Common Issues

#### "No active browser session" Error
```bash
# Make sure to start a browser session first
{
  "tool": "start_browser",
  "arguments": {"browser": "chrome"}
}
```

#### Chrome/Firefox Not Found
```bash
# Install browsers manually if needed
# Ubuntu/Debian:
sudo apt install google-chrome-stable firefox

# Or use Docker which includes all browsers
docker-compose up selenium-mcp
```

#### Permission Denied in Docker
```bash
# Make sure to use proper security settings
docker run --security-opt seccomp=unconfined --cap-add=SYS_ADMIN selenium-mcp
```

#### Element Not Found
- Increase timeout values
- Try different locator strategies
- Use `wait_for_condition` for dynamic content
- Check if element is in an iframe

### Debug Mode
```bash
# Enable debug logging
SELENIUM_LOG_LEVEL=DEBUG uv run selenium-mcp

# Or in Docker
docker-compose up selenium-mcp-dev
```

### Headful Mode for Debugging
```bash
# Start browser in headed mode to see what's happening
{
  "tool": "start_browser",
  "arguments": {
    "browser": "chrome",
    "options": {
      "headless": false,
      "window_size": [1920, 1080]
    }
  }
}
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Selenium WebDriver](https://selenium.dev/) for browser automation
- [Model Context Protocol](https://modelcontextprotocol.io/) for standardized AI integration
- [FastMCP](https://github.com/modelcontextprotocol/python-sdk) for the Python MCP framework
- [webdriver-manager](https://github.com/SergeyPirogov/webdriver_manager) for automatic driver management

## 📞 Support

- 📖 [Documentation](https://github.com/your-org/selenium-mcp-server/wiki)
- 🐛 [Issue Tracker](https://github.com/your-org/selenium-mcp-server/issues)
- 💬 [Discussions](https://github.com/your-org/selenium-mcp-server/discussions)

---

**Happy Automating! 🎉**