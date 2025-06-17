import { resetBrowserState } from "../../toolHandler.js";
import { ToolContext, ToolResponse, createErrorResponse, createSuccessResponse } from "../common/types.js";
import { BrowserToolBase } from "./base.js";

/**
 * Tool for getting the visible text content of the current page
 */
export class VisibleTextTool extends BrowserToolBase {
  /**
   * Execute the visible text page tool
   */
  async execute(args: any, context: ToolContext): Promise<ToolResponse> {
    // Check if browser is available
    if (!context.browser || !context.browser.isConnected()) {
      // If browser is not connected, we need to reset the state to force recreation
      resetBrowserState();
      return createErrorResponse(
        "Browser is not connected. The connection has been reset - please retry your navigation."
      );
    }

    // Check if page is available and not closed
    if (!context.page || context.page.isClosed()) {
      return createErrorResponse(
        "Page is not available or has been closed. Please retry your navigation."
      );
    }
    return this.safeExecute(context, async (page) => {
      try {
        const visibleText = await page!.evaluate(() => {
          const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            {
              acceptNode: (node) => {
                const style = window.getComputedStyle(node.parentElement!);
                return (style.display !== "none" && style.visibility !== "hidden")
                  ? NodeFilter.FILTER_ACCEPT
                  : NodeFilter.FILTER_REJECT;
              },
            }
          );
          let text = "";
          let node;
          while ((node = walker.nextNode())) {
            const trimmedText = node.textContent?.trim();
            if (trimmedText) {
              text += trimmedText + "\n";
            }
          }
          return text.trim();
        });
        return createSuccessResponse(`Visible text content:\n${visibleText}`);
      } catch (error) {
        return createErrorResponse(`Failed to get visible text content: ${(error as Error).message}`);
      }
    });
  }
}

/**
 * Tool for getting the visible HTML content of the current page
 */
export class VisibleHtmlTool extends BrowserToolBase {
  /**
   * Execute the visible HTML page tool
   */
  async execute(args: any, context: ToolContext): Promise<ToolResponse> {
    // Check if browser is available
    if (!context.browser || !context.browser.isConnected()) {
      // If browser is not connected, we need to reset the state to force recreation
      resetBrowserState();
      return createErrorResponse(
        "Browser is not connected. The connection has been reset - please retry your navigation."
      );
    }

    // Check if page is available and not closed
    if (!context.page || context.page.isClosed()) {
      return createErrorResponse(
        "Page is not available or has been closed. Please retry your navigation."
      );
    }
    return this.safeExecute(context, async (page) => {
      try {
        const htmlContent = await page!.content();
        return createSuccessResponse(`HTML content:\n${htmlContent}`);
      } catch (error) {
        return createErrorResponse(`Failed to get visible HTML content: ${(error as Error).message}`);
      }
    });
  }
}