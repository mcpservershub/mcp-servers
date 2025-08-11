#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ErrorCode,
  McpError
} from '@modelcontextprotocol/sdk/types.js';
import { BrowserManager } from './browser-manager.js';
import { PuppeteerTools } from './tools.js';

const PACKAGE_NAME = '@mcp/puppeteer-server';
const PACKAGE_VERSION = '1.0.0';

class PuppeteerMCPServer {
  private server: Server;
  private browserManager: BrowserManager;
  private tools: PuppeteerTools;

  constructor() {
    this.server = new Server(
      {
        name: PACKAGE_NAME,
        version: PACKAGE_VERSION,
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    const headless = process.env.PUPPETEER_HEADLESS !== 'false';
    this.browserManager = new BrowserManager(headless);
    this.tools = new PuppeteerTools(() => this.browserManager.getPage());

    this.setupHandlers();
    this.setupCleanup();
  }

  private setupHandlers(): void {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'puppeteer_navigate',
          description: 'Navigate to a URL',
          inputSchema: {
            type: 'object',
            properties: {
              url: { type: 'string', description: 'The URL to navigate to' },
              waitUntil: {
                type: 'string',
                enum: ['load', 'domcontentloaded', 'networkidle0', 'networkidle2'],
                description: 'When to consider navigation succeeded',
                default: 'networkidle2'
              },
              output_file: { type: 'string', description: 'Optional file path to save navigation info' }
            },
            required: ['url']
          }
        },
        {
          name: 'puppeteer_screenshot',
          description: 'Take a screenshot of the current page or specific element',
          inputSchema: {
            type: 'object',
            properties: {
              selector: { type: 'string', description: 'CSS selector of element to screenshot' },
              fullPage: { type: 'boolean', description: 'Capture full page', default: false },
              format: {
                type: 'string',
                enum: ['png', 'jpeg', 'webp'],
                description: 'Screenshot format',
                default: 'png'
              },
              quality: {
                type: 'number',
                description: 'Quality (0-100, only for jpeg/webp)',
                minimum: 0,
                maximum: 100
              },
              output_file: { type: 'string', description: 'Optional file path to save screenshot' }
            }
          }
        },
        {
          name: 'puppeteer_click',
          description: 'Click on an element',
          inputSchema: {
            type: 'object',
            properties: {
              selector: { type: 'string', description: 'CSS selector of element to click' },
              clickCount: { type: 'number', description: 'Number of clicks', default: 1 },
              delay: { type: 'number', description: 'Delay between clicks in ms', default: 0 }
            },
            required: ['selector']
          }
        },
        {
          name: 'puppeteer_type',
          description: 'Type text into an input field',
          inputSchema: {
            type: 'object',
            properties: {
              selector: { type: 'string', description: 'CSS selector of input element' },
              text: { type: 'string', description: 'Text to type' },
              delay: { type: 'number', description: 'Delay between keystrokes in ms', default: 0 },
              clear: { type: 'boolean', description: 'Clear field before typing', default: false }
            },
            required: ['selector', 'text']
          }
        },
        {
          name: 'puppeteer_wait_for_selector',
          description: 'Wait for an element to appear',
          inputSchema: {
            type: 'object',
            properties: {
              selector: { type: 'string', description: 'CSS selector to wait for' },
              timeout: { type: 'number', description: 'Maximum wait time in ms', default: 30000 },
              visible: { type: 'boolean', description: 'Wait for element to be visible', default: true },
              hidden: { type: 'boolean', description: 'Wait for element to be hidden', default: false }
            },
            required: ['selector']
          }
        },
        {
          name: 'puppeteer_evaluate',
          description: 'Execute JavaScript in the browser context',
          inputSchema: {
            type: 'object',
            properties: {
              script: { type: 'string', description: 'JavaScript code to execute' },
              args: { type: 'array', description: 'Arguments to pass to the script', default: [] },
              output_file: { type: 'string', description: 'Optional file path to save script result' }
            },
            required: ['script']
          }
        },
        {
          name: 'puppeteer_get_content',
          description: 'Get text or HTML content from the page',
          inputSchema: {
            type: 'object',
            properties: {
              selector: { type: 'string', description: 'CSS selector (optional, defaults to body)' },
              type: {
                type: 'string',
                enum: ['text', 'html', 'value'],
                description: 'Type of content to get',
                default: 'text'
              },
              output_file: { type: 'string', description: 'Optional file path to save content' }
            }
          }
        },
        {
          name: 'puppeteer_scroll',
          description: 'Scroll the page',
          inputSchema: {
            type: 'object',
            properties: {
              x: { type: 'number', description: 'Horizontal scroll position', default: 0 },
              y: { type: 'number', description: 'Vertical scroll position', default: 0 },
              smooth: { type: 'boolean', description: 'Use smooth scrolling', default: true }
            }
          }
        },
        {
          name: 'puppeteer_set_viewport',
          description: 'Set the viewport size',
          inputSchema: {
            type: 'object',
            properties: {
              width: { type: 'number', description: 'Viewport width in pixels' },
              height: { type: 'number', description: 'Viewport height in pixels' },
              deviceScaleFactor: { type: 'number', description: 'Device scale factor', default: 1 },
              isMobile: { type: 'boolean', description: 'Whether meta viewport tag is taken into account', default: false },
              hasTouch: { type: 'boolean', description: 'Whether viewport supports touch events', default: false }
            },
            required: ['width', 'height']
          }
        },
        {
          name: 'puppeteer_pdf',
          description: 'Generate PDF from the current page',
          inputSchema: {
            type: 'object',
            properties: {
              path: { type: 'string', description: 'File path to save PDF' },
              format: {
                type: 'string',
                enum: ['Letter', 'Legal', 'Tabloid', 'Ledger', 'A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6'],
                description: 'Paper format'
              },
              width: { type: 'string', description: 'Paper width (e.g., "8.5in", "21cm")' },
              height: { type: 'string', description: 'Paper height' },
              landscape: { type: 'boolean', description: 'Paper orientation', default: false },
              printBackground: { type: 'boolean', description: 'Print background graphics', default: false },
              scale: { type: 'number', description: 'Scale of the page rendering', default: 1 },
              output_file: { type: 'string', description: 'Optional file path to save PDF' }
            }
          }
        },
        {
          name: 'puppeteer_fill_form',
          description: 'Fill multiple form fields at once',
          inputSchema: {
            type: 'object',
            properties: {
              fields: {
                type: 'object',
                description: 'Object mapping CSS selectors to values',
                additionalProperties: { type: 'string' }
              },
              output_file: { type: 'string', description: 'Optional file path to save form data' }
            },
            required: ['fields']
          }
        },
        {
          name: 'puppeteer_extract_links',
          description: 'Extract all links from the page',
          inputSchema: {
            type: 'object',
            properties: {
              selector: { type: 'string', description: 'CSS selector for links', default: 'a' },
              includeText: { type: 'boolean', description: 'Include link text', default: true },
              output_file: { type: 'string', description: 'Optional file path to save extracted links' }
            }
          }
        },
        {
          name: 'puppeteer_close_page',
          description: 'Close the current page',
          inputSchema: {
            type: 'object',
            properties: {}
          }
        }
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      try {
        if (!this.browserManager.isInitialized()) {
          await this.browserManager.initialize();
        }

        const { name, arguments: args } = request.params;

        let result: unknown;

        switch (name) {
          case 'puppeteer_navigate':
            result = await this.tools.navigate(args);
            break;
          case 'puppeteer_screenshot':
            result = await this.tools.screenshot(args);
            break;
          case 'puppeteer_click':
            result = await this.tools.click(args);
            break;
          case 'puppeteer_type':
            result = await this.tools.type(args);
            break;
          case 'puppeteer_wait_for_selector':
            result = await this.tools.waitForSelector(args);
            break;
          case 'puppeteer_evaluate':
            result = await this.tools.evaluate(args);
            break;
          case 'puppeteer_get_content':
            result = await this.tools.getContent(args);
            break;
          case 'puppeteer_scroll':
            result = await this.tools.scroll(args);
            break;
          case 'puppeteer_set_viewport':
            result = await this.tools.setViewport(args);
            break;
          case 'puppeteer_pdf':
            result = await this.tools.generatePdf(args);
            break;
          case 'puppeteer_fill_form':
            result = await this.tools.fillForm(args);
            break;
          case 'puppeteer_extract_links':
            result = await this.tools.extractLinks(args);
            break;
          case 'puppeteer_close_page':
            result = await this.tools.closePage();
            await this.browserManager.closeCurrentPage();
            break;
          default:
            throw new McpError(
              ErrorCode.MethodNotFound,
              `Tool not found: ${name}`
            );
        }

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      } catch (error) {
        if (error instanceof McpError) {
          throw error;
        }
        
        const errorMessage = error instanceof Error ? error.message : String(error);
        
        if (errorMessage.includes('Invalid')) {
          throw new McpError(
            ErrorCode.InvalidParams,
            errorMessage
          );
        }
        
        throw new McpError(
          ErrorCode.InternalError,
          `Tool execution failed: ${errorMessage}`
        );
      }
    });
  }

  private setupCleanup(): void {
    const cleanup = async () => {
      await this.browserManager.close();
      process.exit(0);
    };

    process.on('SIGINT', cleanup);
    process.on('SIGTERM', cleanup);
    process.on('exit', () => {
      this.browserManager.close();
    });
  }

  async run(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error(`${PACKAGE_NAME} v${PACKAGE_VERSION} - MCP server running`);
  }
}

const server = new PuppeteerMCPServer();
server.run().catch((error) => {
  console.error('Server error:', error);
  process.exit(1);
});