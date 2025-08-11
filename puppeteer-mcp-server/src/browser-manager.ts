import puppeteer, { Browser, Page } from 'puppeteer';

export class BrowserManager {
  private browser: Browser | null = null;
  private page: Page | null = null;
  private isHeadless: boolean;

  constructor(headless: boolean = true) {
    this.isHeadless = headless;
  }

  async initialize(): Promise<void> {
    if (this.browser) {
      return;
    }

    try {
      this.browser = await puppeteer.launch({
        headless: this.isHeadless,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-accelerated-2d-canvas',
          '--no-first-run',
          '--no-zygote',
          '--single-process',
          '--disable-gpu'
        ]
      });

      this.page = await this.browser.newPage();
      
      await this.page.setUserAgent(
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      );
    } catch (error) {
      throw new Error(`Failed to initialize browser: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async getPage(): Promise<Page> {
    if (!this.page) {
      await this.initialize();
    }
    if (!this.page) {
      throw new Error('Browser page not initialized');
    }
    return this.page;
  }

  async newPage(): Promise<Page> {
    if (!this.browser) {
      await this.initialize();
    }
    if (!this.browser) {
      throw new Error('Browser not initialized');
    }
    const newPage = await this.browser.newPage();
    await newPage.setUserAgent(
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    );
    return newPage;
  }

  async closeCurrentPage(): Promise<void> {
    if (this.page && !this.page.isClosed()) {
      await this.page.close();
      this.page = null;
    }
  }

  async close(): Promise<void> {
    if (this.page && !this.page.isClosed()) {
      await this.page.close();
    }
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
      this.page = null;
    }
  }

  isInitialized(): boolean {
    return this.browser !== null;
  }
}