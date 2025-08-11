import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import { BrowserManager } from './browser-manager.js';
import { PuppeteerTools } from './tools.js';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';

describe('Puppeteer MCP Server', () => {
  let browserManager: BrowserManager;
  let tools: PuppeteerTools;

  beforeAll(async () => {
    browserManager = new BrowserManager(true);
    await browserManager.initialize();
    tools = new PuppeteerTools(() => browserManager.getPage());
  });

  afterAll(async () => {
    await browserManager.close();
  });

  beforeEach(async () => {
    // Only navigate if page exists and is not closed
    try {
      const page = await browserManager.getPage();
      if (!page.isClosed()) {
        await page.goto('about:blank');
      }
    } catch {
      // Page might be closed from previous test
    }
  });

  describe('Navigation Tool', () => {
    it('should navigate to a URL', async () => {
      const result = await tools.navigate({
        url: 'https://example.com',
        waitUntil: 'networkidle2'
      });

      expect(result).toHaveProperty('url');
      expect(result).toHaveProperty('title');
      expect(result).toHaveProperty('status');
      expect(result.url).toContain('example.com');
      expect(result.status).toBe(200);
    });

    it('should reject invalid URL', async () => {
      await expect(tools.navigate({
        url: 'not-a-url'
      })).rejects.toThrow();
    });
  });

  describe('Screenshot Tool', () => {
    it('should take a full page screenshot', async () => {
      await tools.navigate({ url: 'https://example.com' });
      
      const result = await tools.screenshot({
        fullPage: true,
        format: 'png'
      });

      expect(result).toHaveProperty('screenshot');
      expect(result).toHaveProperty('timestamp');
      expect(result.screenshot).toMatch(/^data:image\/png;base64,/);
    });

    it('should take element screenshot', async () => {
      await tools.navigate({ url: 'https://example.com' });
      
      const result = await tools.screenshot({
        selector: 'h1',
        format: 'jpeg',
        quality: 80
      });

      expect(result).toHaveProperty('screenshot');
      expect(result.screenshot).toMatch(/^data:image\/jpeg;base64,/);
    });
  });

  describe('Click Tool', () => {
    it('should click on an element', async () => {
      await tools.navigate({ url: 'https://example.com' });
      
      const result = await tools.click({
        selector: 'a',
        clickCount: 1
      });

      expect(result).toHaveProperty('success');
      expect(result.success).toBe(true);
      expect(result.selector).toBe('a');
    });

    it('should fail on non-existent element', async () => {
      await expect(tools.click({
        selector: '#non-existent-element'
      })).rejects.toThrow();
    });
  });

  describe('Type Tool', () => {
    it('should type text into input', async () => {
      const page = await browserManager.getPage();
      await page.setContent('<input id="test-input" />');
      
      const result = await tools.type({
        selector: '#test-input',
        text: 'Hello World',
        delay: 10
      });

      expect(result).toHaveProperty('success');
      expect(result.success).toBe(true);
      expect(result.text).toBe('Hello World');
      
      const value = await page.$eval('#test-input', el => (el as HTMLInputElement).value);
      expect(value).toBe('Hello World');
    });

    it('should clear before typing', async () => {
      const page = await browserManager.getPage();
      await page.setContent('<input id="test-input" value="old text" />');
      
      await tools.type({
        selector: '#test-input',
        text: 'New Text',
        clear: true
      });

      const value = await page.$eval('#test-input', el => (el as HTMLInputElement).value);
      expect(value).toBe('New Text');
    });
  });

  describe('Wait For Selector Tool', () => {
    it('should wait for element to appear', async () => {
      const page = await browserManager.getPage();
      await page.setContent('<div id="test" style="display:block">Test</div>');
      
      const result = await tools.waitForSelector({
        selector: '#test',
        timeout: 5000,
        visible: false  // Don't check visibility, just existence
      });

      expect(result).toHaveProperty('found');
      expect(result.found).toBe(true);
    });

    it('should timeout on non-existent element', async () => {
      const result = await tools.waitForSelector({
        selector: '#non-existent',
        timeout: 1000,
        visible: false
      });

      expect(result.found).toBe(false);
    });
  });

  describe('Evaluate Tool', () => {
    it('should execute JavaScript', async () => {
      const result = await tools.evaluate({
        script: 'return 2 + 2',
        args: []
      });

      expect(result).toHaveProperty('result');
      expect(result.result).toBe(4);
    });

    it('should pass arguments', async () => {
      const result = await tools.evaluate({
        script: 'return args[0] + args[1]',
        args: [10, 20]
      });

      expect(result.result).toBe(30);
    });
  });

  describe('Get Content Tool', () => {
    it('should get page text content', async () => {
      const page = await browserManager.getPage();
      await page.setContent('<div>Test Content</div>');
      
      const result = await tools.getContent({
        type: 'text'
      });

      expect(result).toHaveProperty('content');
      expect(result.content).toContain('Test Content');
    });

    it('should get element HTML', async () => {
      const page = await browserManager.getPage();
      await page.setContent('<div id="test"><span>Inner</span></div>');
      
      const result = await tools.getContent({
        selector: '#test',
        type: 'html'
      });

      expect(result.content).toBe('<span>Inner</span>');
    });

    it('should get input value', async () => {
      const page = await browserManager.getPage();
      await page.setContent('<input id="test" value="test value" />');
      
      const result = await tools.getContent({
        selector: '#test',
        type: 'value'
      });

      expect(result.content).toBe('test value');
    });
  });

  describe('Scroll Tool', () => {
    it('should scroll to position', async () => {
      const page = await browserManager.getPage();
      await page.setContent('<div style="height: 3000px">Long content</div>');
      
      const result = await tools.scroll({
        x: 0,
        y: 500,
        smooth: false
      });

      expect(result).toHaveProperty('success');
      expect(result.success).toBe(true);
      expect(result.position.y).toBe(500);
    });
  });

  describe('Set Viewport Tool', () => {
    it('should set viewport size', async () => {
      const result = await tools.setViewport({
        width: 1920,
        height: 1080,
        deviceScaleFactor: 2,
        isMobile: false
      });

      expect(result).toHaveProperty('success');
      expect(result.success).toBe(true);
      expect(result.viewport.width).toBe(1920);
      expect(result.viewport.height).toBe(1080);
    });
  });

  describe('PDF Tool', () => {
    it('should generate PDF', async () => {
      await tools.navigate({ url: 'https://example.com' });
      
      const result = await tools.generatePdf({
        format: 'A4',
        printBackground: true,
        landscape: false
      });

      expect(result).toHaveProperty('pdf');
      expect(result).toHaveProperty('pages');
      expect(result.pdf).toMatch(/^data:application\/pdf;base64,/);
    });
  });

  describe('Fill Form Tool', () => {
    it('should fill multiple form fields', async () => {
      const page = await browserManager.getPage();
      await page.setContent(`
        <form>
          <input id="name" name="name" />
          <input id="email" name="email" />
          <textarea id="message"></textarea>
        </form>
      `);
      
      const result = await tools.fillForm({
        fields: {
          '#name': 'John Doe',
          '#email': 'john@example.com',
          '#message': 'Test message'
        }
      });

      expect(result).toHaveProperty('success');
      expect(result.success).toBe(true);
      expect(result.filled).toHaveProperty('#name');
      
      const nameValue = await page.$eval('#name', el => (el as HTMLInputElement).value);
      expect(nameValue).toBe('John Doe');
    });

    it('should handle select elements', async () => {
      const page = await browserManager.getPage();
      await page.setContent(`
        <select id="country">
          <option value="us">USA</option>
          <option value="uk">UK</option>
        </select>
      `);
      
      const result = await tools.fillForm({
        fields: {
          '#country': 'uk'
        }
      });

      const value = await page.$eval('#country', el => (el as HTMLSelectElement).value);
      expect(value).toBe('uk');
    });
  });

  describe('Extract Links Tool', () => {
    it('should extract all links', async () => {
      const page = await browserManager.getPage();
      await page.setContent(`
        <a href="https://example.com">Example</a>
        <a href="https://google.com">Google</a>
      `);
      
      const result = await tools.extractLinks({
        selector: 'a',
        includeText: true
      });

      expect(result).toHaveProperty('links');
      expect(result.links).toHaveLength(2);
      expect(result.links[0]).toHaveProperty('href');
      expect(result.links[0]).toHaveProperty('text');
      expect(result.links[0].text).toBe('Example');
    });
  });

  describe('Close Page Tool', () => {
    it('should close the current page', async () => {
      // Create a new page for this test
      await browserManager.newPage();
      const result = await tools.closePage();
      
      expect(result).toHaveProperty('success');
      expect(result.success).toBe(true);
    });
  });

  describe('Input Validation', () => {
    it('should validate navigate input', async () => {
      // Ensure page is ready
      await browserManager.getPage();
      await expect(tools.navigate({
        url: 123 as any
      })).rejects.toThrow();
    });

    it('should validate click selector', async () => {
      await browserManager.getPage();
      await expect(tools.click({
        selector: ''
      })).rejects.toThrow('Selector is required');
    });

    it('should validate type input', async () => {
      await browserManager.getPage();
      await expect(tools.type({
        selector: '#test',
        text: ''
      })).rejects.toThrow('Text is required');
    });

    it('should validate viewport dimensions', async () => {
      await browserManager.getPage();
      await expect(tools.setViewport({
        width: -1,
        height: 1080
      })).rejects.toThrow();
    });

    it('should validate form fields', async () => {
      await browserManager.getPage();
      await expect(tools.fillForm({
        fields: {}
      })).rejects.toThrow('At least one field is required');
    });
  });
});