import { Page } from 'puppeteer';
import { writeFile } from 'fs/promises';
import { dirname } from 'path';
import { mkdir } from 'fs/promises';
import {
  NavigateSchema,
  ScreenshotSchema,
  ClickSchema,
  TypeSchema,
  WaitForSelectorSchema,
  EvaluateSchema,
  GetContentSchema,
  ScrollSchema,
  SetViewportSchema,
  PdfSchema,
  FillFormSchema,
  ExtractLinksSchema
} from './schemas.js';

export class PuppeteerTools {
  constructor(private getPage: () => Promise<Page>) {}

  private async saveToFile(filePath: string, content: string | Buffer): Promise<void> {
    try {
      const dir = dirname(filePath);
      if (dir && dir !== '.') {
        await mkdir(dir, { recursive: true });
      }
      await writeFile(filePath, content);
    } catch (error) {
      throw new Error(`Failed to save to file: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async navigate(input: unknown): Promise<{ url: string; title: string; status: number }> {
    const params = NavigateSchema.parse(input);
    const page = await this.getPage();
    
    try {
      const response = await page.goto(params.url, {
        waitUntil: params.waitUntil,
        timeout: 30000
      });
      
      if (!response) {
        throw new Error('Navigation failed: no response received');
      }
      
      const title = await page.title();
      
      const result = {
        url: page.url(),
        title,
        status: response.status()
      };
      
      if (params.output_file) {
        await this.saveToFile(params.output_file, JSON.stringify(result, null, 2));
      }
      
      return result;
    } catch (error) {
      throw new Error(`Navigation failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async screenshot(input: unknown): Promise<{ screenshot: string; timestamp: string; saved_to?: string }> {
    const params = ScreenshotSchema.parse(input);
    const page = await this.getPage();
    
    try {
      let screenshotOptions: any = {
        encoding: 'base64',
        fullPage: params.fullPage,
        type: params.format
      };
      
      if (params.quality && params.format !== 'png') {
        screenshotOptions.quality = params.quality;
      }
      
      let screenshot: string;
      let screenshotBuffer: Buffer | undefined;
      
      if (params.output_file) {
        // Get buffer for file saving
        screenshotOptions.encoding = undefined;
        if (params.selector) {
          const element = await page.$(params.selector);
          if (!element) {
            throw new Error(`Element not found: ${params.selector}`);
          }
          screenshotBuffer = await element.screenshot(screenshotOptions) as unknown as Buffer;
        } else {
          screenshotBuffer = await page.screenshot(screenshotOptions) as unknown as Buffer;
        }
        screenshot = screenshotBuffer.toString('base64');
      } else {
        if (params.selector) {
          const element = await page.$(params.selector);
          if (!element) {
            throw new Error(`Element not found: ${params.selector}`);
          }
          screenshot = await element.screenshot(screenshotOptions) as string;
        } else {
          screenshot = await page.screenshot(screenshotOptions) as string;
        }
      }
      
      const result: any = {
        screenshot: `data:image/${params.format};base64,${screenshot}`,
        timestamp: new Date().toISOString()
      };
      
      if (params.output_file && screenshotBuffer) {
        await this.saveToFile(params.output_file, screenshotBuffer);
        result.saved_to = params.output_file;
      }
      
      return result;
    } catch (error) {
      throw new Error(`Screenshot failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async click(input: unknown): Promise<{ success: boolean; selector: string }> {
    const params = ClickSchema.parse(input);
    const page = await this.getPage();
    
    try {
      await page.waitForSelector(params.selector, { timeout: 5000 });
      await page.click(params.selector, {
        clickCount: params.clickCount,
        delay: params.delay
      });
      
      return {
        success: true,
        selector: params.selector
      };
    } catch (error) {
      throw new Error(`Click failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async type(input: unknown): Promise<{ success: boolean; selector: string; text: string }> {
    const params = TypeSchema.parse(input);
    const page = await this.getPage();
    
    try {
      await page.waitForSelector(params.selector, { timeout: 5000 });
      
      if (params.clear) {
        await page.evaluate((selector: string) => {
          const element = document.querySelector(selector) as any;
          if (element) {
            element.value = '';
          }
        }, params.selector);
      }
      
      await page.type(params.selector, params.text, { delay: params.delay });
      
      return {
        success: true,
        selector: params.selector,
        text: params.text
      };
    } catch (error) {
      throw new Error(`Type failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async waitForSelector(input: unknown): Promise<{ found: boolean; selector: string }> {
    const params = WaitForSelectorSchema.parse(input);
    const page = await this.getPage();
    
    try {
      const options: any = {
        timeout: params.timeout
      };
      
      if (params.hidden) {
        options.hidden = true;
      } else if (params.visible) {
        options.visible = true;
      }
      
      await page.waitForSelector(params.selector, options);
      
      return {
        found: true,
        selector: params.selector
      };
    } catch (error) {
      if (error instanceof Error && (error.message.includes('timeout') || error.message.includes('Waiting failed'))) {
        return {
          found: false,
          selector: params.selector
        };
      }
      throw new Error(`Wait for selector failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async evaluate(input: unknown): Promise<{ result: unknown; saved_to?: string }> {
    const params = EvaluateSchema.parse(input);
    const page = await this.getPage();
    
    try {
      const func = new Function('...args', params.script);
      const result = await page.evaluate(func as any, ...params.args);
      
      const output: any = { result };
      
      if (params.output_file) {
        const content = JSON.stringify(result, null, 2);
        await this.saveToFile(params.output_file, content);
        output.saved_to = params.output_file;
      }
      
      return output;
    } catch (error) {
      throw new Error(`Evaluate failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async getContent(input: unknown): Promise<{ content: string; selector?: string; saved_to?: string }> {
    const params = GetContentSchema.parse(input);
    const page = await this.getPage();
    
    try {
      let content: string;
      
      if (params.selector) {
        await page.waitForSelector(params.selector, { timeout: 5000 });
        
        if (params.type === 'text') {
          content = await page.$eval(params.selector, el => el.textContent || '');
        } else if (params.type === 'html') {
          content = await page.$eval(params.selector, el => el.innerHTML);
        } else {
          content = await page.$eval(params.selector, (el: any) => el.value || '');
        }
      } else {
        if (params.type === 'html') {
          content = await page.content();
        } else {
          content = await page.evaluate(() => document.body?.textContent || '');
        }
      }
      
      const result: any = {
        content: content.trim(),
        selector: params.selector
      };
      
      if (params.output_file) {
        await this.saveToFile(params.output_file, content.trim());
        result.saved_to = params.output_file;
      }
      
      return result;
    } catch (error) {
      throw new Error(`Get content failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async scroll(input: unknown): Promise<{ success: boolean; position: { x: number; y: number } }> {
    const params = ScrollSchema.parse(input);
    const page = await this.getPage();
    
    try {
      await page.evaluate((x: number, y: number, smooth: boolean) => {
        if (smooth) {
          window.scrollTo({ top: y, left: x, behavior: 'smooth' });
        } else {
          window.scrollTo(x, y);
        }
      }, params.x, params.y, params.smooth);
      
      await new Promise(resolve => setTimeout(resolve, params.smooth ? 500 : 100));
      
      const position = await page.evaluate(() => ({
        x: window.scrollX,
        y: window.scrollY
      }));
      
      return {
        success: true,
        position
      };
    } catch (error) {
      throw new Error(`Scroll failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async setViewport(input: unknown): Promise<{ success: boolean; viewport: any }> {
    const params = SetViewportSchema.parse(input);
    const page = await this.getPage();
    
    try {
      await page.setViewport({
        width: params.width,
        height: params.height,
        deviceScaleFactor: params.deviceScaleFactor,
        isMobile: params.isMobile,
        hasTouch: params.hasTouch
      });
      
      return {
        success: true,
        viewport: params
      };
    } catch (error) {
      throw new Error(`Set viewport failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async generatePdf(input: unknown): Promise<{ pdf: string; pages: number; saved_to?: string }> {
    const params = PdfSchema.parse(input);
    const page = await this.getPage();
    
    try {
      const pdfOptions: any = {
        printBackground: params.printBackground,
        landscape: params.landscape,
        scale: params.scale
      };
      
      if (params.format) pdfOptions.format = params.format;
      if (params.width) pdfOptions.width = params.width;
      if (params.height) pdfOptions.height = params.height;
      if (params.margin) pdfOptions.margin = params.margin;
      if (params.path) pdfOptions.path = params.path;
      
      const pdfBuffer = await page.pdf(pdfOptions) as Buffer;
      const pdfBase64 = pdfBuffer.toString('base64');
      
      const result: any = {
        pdf: `data:application/pdf;base64,${pdfBase64}`,
        pages: 1
      };
      
      if (params.output_file) {
        await this.saveToFile(params.output_file, pdfBuffer);
        result.saved_to = params.output_file;
      }
      
      return result;
    } catch (error) {
      throw new Error(`PDF generation failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async fillForm(input: unknown): Promise<{ success: boolean; filled: Record<string, string>; saved_to?: string }> {
    const params = FillFormSchema.parse(input);
    const page = await this.getPage();
    
    try {
      const filled: Record<string, string> = {};
      
      for (const [selector, value] of Object.entries(params.fields)) {
        await page.waitForSelector(selector, { timeout: 5000 });
        
        const tagName = await page.$eval(selector, el => el.tagName.toLowerCase());
        
        if (tagName === 'select') {
          await page.select(selector, value);
        } else if (tagName === 'input') {
          const inputType = await page.$eval(selector, (el: any) => el.type);
          
          if (inputType === 'checkbox' || inputType === 'radio') {
            if (value === 'true' || value === '1') {
              await page.click(selector);
            }
          } else {
            await page.evaluate((sel: string) => {
              const element = document.querySelector(sel) as any;
              if (element) element.value = '';
            }, selector);
            await page.type(selector, value);
          }
        } else if (tagName === 'textarea') {
          await page.evaluate((sel: string) => {
            const element = document.querySelector(sel) as any;
            if (element) element.value = '';
          }, selector);
          await page.type(selector, value);
        }
        
        filled[selector] = value;
      }
      
      const result: any = {
        success: true,
        filled
      };
      
      if (params.output_file) {
        const content = JSON.stringify(filled, null, 2);
        await this.saveToFile(params.output_file, content);
        result.saved_to = params.output_file;
      }
      
      return result;
    } catch (error) {
      throw new Error(`Fill form failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async extractLinks(input: unknown): Promise<{ links: Array<{ href: string; text?: string }>; saved_to?: string }> {
    const params = ExtractLinksSchema.parse(input);
    const page = await this.getPage();
    
    try {
      const links = await page.evaluate((selector: string, includeText: boolean) => {
        const elements = document.querySelectorAll(selector);
        return Array.from(elements).map(el => {
          const link = el as any;
          const result: { href: string; text?: string } = {
            href: link.href
          };
          if (includeText) {
            result.text = link.textContent?.trim() || '';
          }
          return result;
        }).filter(link => link.href);
      }, params.selector, params.includeText);
      
      const result: any = { links };
      
      if (params.output_file) {
        const content = JSON.stringify(links, null, 2);
        await this.saveToFile(params.output_file, content);
        result.saved_to = params.output_file;
      }
      
      return result;
    } catch (error) {
      throw new Error(`Extract links failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  async closePage(): Promise<{ success: boolean }> {
    const page = await this.getPage();
    
    try {
      if (!page.isClosed()) {
        await page.close();
      }
      return { success: true };
    } catch (error) {
      throw new Error(`Close page failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
}