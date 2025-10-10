# Enhanced Cypress MCP Server

A powerful Model Context Protocol (MCP) server that analyzes web pages and generates comprehensive Cypress test code with intelligent pattern recognition and Page Object Model generation.

## 🚀 Features

### 🔍 **Intelligent Web Analysis**
- **Element Detection**: Automatically detects buttons, inputs, forms, links, and interactive elements
- **Optimal Selectors**: Generates prioritized selectors (data-testid > id > class > text)
- **Accessibility Analysis**: Identifies ARIA labels, alt texts, and accessibility features
- **Page Structure**: Analyzes navigation, headers, footers, modals, and layout components

### 🧠 **Pattern Recognition**
- **Login Workflows**: Detects username/password forms with validation scenarios
- **Search Functionality**: Identifies search inputs, filters, and sorting options
- **CRUD Operations**: Recognizes create, read, update, delete patterns
- **E-commerce**: Detects checkout flows, product catalogs, and shopping carts
- **Form Validation**: Identifies required fields, pattern validation, and error handling
- **Navigation**: Maps breadcrumbs, menus, and routing patterns

### 📝 **Code Generation**
- **Page Object Models**: Generates clean, maintainable POM classes
- **Test Suites**: Creates comprehensive test cases covering positive and negative scenarios
- **Workflow Methods**: Intelligent workflow generation (login, search, registration)
- **TypeScript Support**: Full TypeScript and JavaScript support
- **Cypress Integration**: Direct file creation in Cypress projects

### 🧪 **Test Coverage**
- **E2E Tests**: End-to-end user journey testing
- **Accessibility Tests**: WCAG compliance and keyboard navigation
- **Performance Tests**: Load time and interaction performance
- **Error Handling**: Network failures, validation errors, edge cases
- **Cross-browser**: Multi-browser compatibility testing

## 📦 Installation

### Option 1: Docker Container (Recommended)

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t enhanced-cypress-mcp-server .
docker run -d --name cypress-mcp-server enhanced-cypress-mcp-server
```

### Option 2: Local Installation

```bash
# Clone or create the project
npm install

# Install dependencies
npm install @modelcontextprotocol/sdk puppeteer cheerio zod uuid fs-extra
```

## 🔧 Usage

### Using as Docker Container

```bash
# Start the server in container
docker-compose up -d

# View logs
docker-compose logs -f cypress-mcp-server

# Connect to the container for debugging
docker-compose exec cypress-mcp-server sh

# Stop the server
docker-compose down
```

### Local Usage

```bash
# Start the server
npm start

# Or for development with auto-restart
npm run dev
```

## 🛠️ MCP Tools Reference

### 1. **analyzePageAndGenerateCypress**
Analyze a web page and generate comprehensive Cypress test code with Page Objects and test suites.

**Parameters:**
- `url` (string, required): URL of the web page to analyze
- `language` (string, optional): Programming language - `"javascript"` or `"typescript"` (default: `"javascript"`)
- `includePageObjects` (boolean, optional): Generate Page Object Model classes (default: `true`)
- `includeTests` (boolean, optional): Generate test suites (default: `true`)
- `testTypes` (array, optional): Types of tests to generate - `["unit", "integration", "e2e", "accessibility", "performance"]` (default: `["e2e"]`)

**Example:**
```javascript
{
  "method": "tools/call",
  "params": {
    "name": "analyzePageAndGenerateCypress",
    "arguments": {
      "url": "https://example.com/login",
      "language": "typescript",
      "includePageObjects": true,
      "includeTests": true,
      "testTypes": ["e2e", "accessibility", "performance"]
    }
  }
}
```

---

### 2. **createCypressFiles**
Create Cypress test files directly in a Cypress project directory with automatic project detection and validation.

**Parameters:**
- `url` (string, required): URL of the web page to analyze
- `projectPath` (string, optional): Project directory path (auto-detected if not provided)
- `language` (string, optional): Programming language - `"javascript"` or `"typescript"` (default: `"javascript"`)
- `pageObjectName` (string, optional): Custom name for the page object class

**Example:**
```javascript
{
  "method": "tools/call",
  "params": {
    "name": "createCypressFiles",
    "arguments": {
      "url": "https://example.com/dashboard",
      "projectPath": "/path/to/cypress/project",
      "language": "typescript",
      "pageObjectName": "DashboardPage"
    }
  }
}
```

---

### 3. **generateCypressPageObject**
Generate only the Page Object Model class for a specific URL with workflow methods.

**Parameters:**
- `url` (string, required): URL of the web page to analyze
- `className` (string, optional): Custom class name for the page object
- `language` (string, optional): Programming language - `"javascript"` or `"typescript"` (default: `"javascript"`)
- `includeWorkflows` (boolean, optional): Include workflow methods like login, search, etc. (default: `true`)

**Example:**
```javascript
{
  "method": "tools/call",
  "params": {
    "name": "generateCypressPageObject",
    "arguments": {
      "url": "https://example.com/profile",
      "className": "UserProfilePage",
      "language": "javascript",
      "includeWorkflows": true
    }
  }
}
```

---

### 4. **analyzeElement**
Perform deep analysis of a specific element on a web page including context, properties, and accessibility information.

**Parameters:**
- `url` (string, required): URL of the web page containing the element
- `selector` (string, required): CSS selector or XPath for the target element
- `includeContext` (boolean, optional): Include surrounding context like parent, siblings, and children (default: `true`)

**Example:**
```javascript
{
  "method": "tools/call",
  "params": {
    "name": "analyzeElement",
    "arguments": {
      "url": "https://example.com/form",
      "selector": "#submit-button",
      "includeContext": true
    }
  }
}
```

---

### 5. **detectTestPatterns**
Identify testing patterns and workflows on a web page to understand the testing strategy needed.

**Parameters:**
- `url` (string, required): URL of the web page to analyze for patterns

**Example:**
```javascript
{
  "method": "tools/call",
  "params": {
    "name": "detectTestPatterns",
    "arguments": {
      "url": "https://example.com/shop"
    }
  }
}
```

**Returns patterns like:**
- Login workflows (username/password forms)
- Search functionality (search inputs, filters)
- CRUD operations (create, read, update, delete)
- E-commerce patterns (checkout, cart, products)
- Form validation patterns
- Navigation patterns
- File upload patterns
- Modal/dialog patterns
- Pagination patterns
- Data table patterns

---

## 🐳 Docker Configuration

The server includes optimized Docker configuration for containerized deployment:

### Docker Features:
- **Alpine Linux base** for minimal footprint
- **Puppeteer with Chromium** pre-installed
- **Non-root user** for security
- **Health checks** for monitoring
- **Volume mounts** for generated test files
- **Resource limits** for production use

### Docker Commands:
```bash
# Build the container
docker build -t enhanced-cypress-mcp-server .

# Run with volume mounting for output files
docker run -d \
  --name cypress-mcp-server \
  -v $(pwd)/generated-tests:/app/output:rw \
  enhanced-cypress-mcp-server

# Using Docker Compose (recommended)
docker-compose up -d

# View container logs
docker logs -f cypress-mcp-server

# Access container shell
docker exec -it cypress-mcp-server sh
```

### Volume Mounts:
- `/app/output`: Mount point for generated test files
- `/app/data`: Persistent data storage
- Source code mounting available in development mode

## 📋 Generated Code Examples

### Page Object Model

```javascript
export class LoginPage {
  // Element selectors
  elements = {
    usernameInput: '[data-testid="username"]',
    passwordInput: '[data-testid="password"]',
    loginButton: '#login-btn',
    errorMessage: '.error-text'
  };

  // Navigation
  visit() {
    cy.visit('https://example.com/login');
    return this;
  }

  // Element getters
  get UsernameInput() {
    return cy.get(this.elements.usernameInput);
  }

  get PasswordInput() {
    return cy.get(this.elements.passwordInput);
  }

  // Element actions
  typeUsernameInput(text) {
    this.UsernameInput.clear().type(text);
    return this;
  }

  clickLoginButton() {
    this.LoginButton.click();
    return this;
  }

  // Workflow methods
  login(username, password) {
    if (username) this.typeUsernameInput(username);
    if (password) this.typePasswordInput(password);
    this.clickLoginButton();
    return this;
  }
}
```

### Test Suite

```javascript
import { LoginPage } from '../support/pages/LoginPage';

describe('LoginPage Tests', () => {
  let page;

  beforeEach(() => {
    page = new LoginPage();
    page.visit();
  });

  describe('Login Workflow', () => {
    it('should login with valid credentials', () => {
      page.login('user@example.com', 'password123');
      cy.url().should('not.include', '/login');
    });

    it('should show error with invalid credentials', () => {
      page.login('invalid@example.com', 'wrongpass');
      cy.get('.error-text').should('be.visible');
    });
  });

  describe('Form Validation', () => {
    it('should validate required username field', () => {
      page.clickLoginButton();
      cy.get('[data-testid="username"]').should('have.class', 'error');
    });
  });
});
```

## 🏗️ Project Structure

```
cypress-mcp-server/
├── src/
│   ├── index.js                    # Main MCP server
│   ├── element-analyzer.js         # Web page analysis
│   ├── test-pattern-detector.js    # Pattern recognition
│   ├── code-generator.js          # Code generation
│   └── file-manager.js            # File operations
├── test/
│   └── test-server.js             # Test examples
├── package.json
└── README.md
```

## 🎯 Detected Patterns

### Login Pattern
- Username/email fields
- Password fields
- Submit buttons
- Remember me checkboxes
- Forgot password links

### Search Pattern
- Search inputs
- Filter options
- Sort dropdowns
- Results containers
- Pagination controls

### CRUD Pattern
- Data tables
- Create/Add buttons
- Edit/Update actions
- Delete confirmations
- Form submissions

### E-commerce Pattern
- Product catalogs
- Add to cart buttons
- Checkout flows
- Payment forms
- Order summaries

## ⚙️ Configuration

### Cypress Configuration
The server automatically generates `cypress.config.js` or `cypress.config.ts` with optimized settings:

```javascript
import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    viewportWidth: 1920,
    viewportHeight: 1080,
    video: true,
    screenshotOnRunFailure: true,
    defaultCommandTimeout: 10000,
    pageLoadTimeout: 30000,
    setupNodeEvents(on, config) {
      return config;
    },
  },
});
```

## 🚀 Getting Started

### Option A: Docker Container (Recommended)

1. **Build and Start the Container**
   ```bash
   # Using Docker Compose (easiest)
   docker-compose up -d

   # Or build manually
   docker build -t enhanced-cypress-mcp-server .
   docker run -d \
     --name cypress-mcp-server \
     -v $(pwd)/generated-tests:/app/output:rw \
     enhanced-cypress-mcp-server
   ```

2. **Verify Container is Running**
   ```bash
   # Check container status
   docker-compose ps

   # View logs
   docker-compose logs -f cypress-mcp-server
   ```

3. **Connect Your MCP Client**
   - The server runs inside the container using stdio transport
   - Connect to the containerized process
   - Generated files will be available in the mounted volume `./generated-tests/`

### Option B: Local Installation

1. **Install the MCP Server**
   ```bash
   npm install
   ```

2. **Start the Server**
   ```bash
   npm start
   ```

3. **Connect Your MCP Client**
   - Use stdio transport
   - Connect to the running server process

### Usage Examples

4. **Generate Tests**
   ```javascript
   // Analyze a login page and generate complete test suite
   {
     "method": "tools/call",
     "params": {
       "name": "analyzePageAndGenerateCypress",
       "arguments": {
         "url": "https://myapp.com/login",
         "language": "typescript",
         "testTypes": ["e2e", "accessibility"]
       }
     }
   }
   ```

5. **Create Project Files**
   ```javascript
   // Create files directly in your Cypress project
   {
     "method": "tools/call",
     "params": {
       "name": "createCypressFiles",
       "arguments": {
         "url": "https://myapp.com/dashboard",
         "projectPath": "/path/to/cypress/project"
       }
     }
   }
   ```

### Container Management

```bash
# Start the server
docker-compose up -d

# Stop the server
docker-compose down

# Restart the server
docker-compose restart cypress-mcp-server

# View real-time logs
docker-compose logs -f

# Access container shell for debugging
docker-compose exec cypress-mcp-server sh

# Remove container and volumes
docker-compose down -v
```

## 🧪 Best Practices

### Element Selection Priority
1. `[data-testid="..."]` - Most reliable
2. `#unique-id` - Good for stable elements
3. `.unique-class` - Acceptable for styling-independent classes
4. Text content - For buttons and links with stable text
5. CSS selectors - Last resort

### Test Organization
- **Page Objects**: Store in `cypress/support/pages/`
- **Tests**: Organize in `cypress/e2e/` by feature
- **Fixtures**: Use `cypress/fixtures/` for test data
- **Commands**: Custom commands in `cypress/support/commands.js`

### Workflow Methods
The server generates intelligent workflow methods based on detected patterns:
- `login(username, password)` - Complete login flow
- `search(query)` - Search with optional filters
- `register(userData)` - User registration flow
- `checkout(items)` - E-commerce checkout process

## 🔧 Advanced Features

### Custom Element Detection
Add `data-testid` attributes to your HTML for optimal selector generation:

```html
<button data-testid="submit-form" class="btn btn-primary">
  Submit
</button>
```

### Pattern Customization
The pattern detector can be extended to recognize custom workflows specific to your application.

### Multi-language Support
- Full TypeScript support with proper typing
- JavaScript ES6+ with modern syntax
- Consistent code style and formatting

## 📊 Analytics & Reporting

The server provides detailed analysis reports including:
- Element count and types
- Accessibility compliance score
- Pattern detection confidence levels
- Test coverage recommendations
- Performance optimization suggestions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the test examples in `/test/test-server.js`
2. Review the generated code for implementation details
3. Open an issue for bugs or feature requests

---

**Happy Testing with Cypress! 🎯**