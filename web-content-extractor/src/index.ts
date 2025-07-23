#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { extractContent } from "@wrtnlabs/web-content-extractor";
import fetch from "node-fetch";
import { promises as fs } from "fs";
import { dirname } from "path";
import * as path from "path";

// Fallback content extraction function for when the library fails
function fallbackExtractContent(html: string): string {
  // Simple HTML content extraction as fallback
  try {
    // Remove script and style tags
    let cleanHtml = html.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '');
    cleanHtml = cleanHtml.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '');
    
    // Remove HTML tags and get text content
    const textContent = cleanHtml.replace(/<[^>]*>/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
    
    return textContent;
  } catch (error) {
    return 'Failed to extract content using fallback method';
  }
}

const GetContentArgsSchema = z.object({
  url: z.string().url("Must be a valid URL"),
  output_file_path: z.string().min(1, "Output file path is required")
});

// extractContent returns a simple string with the main content

class WebContentExtractorMCPServer {
  private server: McpServer;

  constructor() {
    this.server = new McpServer({
      name: "web-content-extractor-mcp-server",
      version: "1.0.0"
    });

    this.setupTools();
  }

  private setupTools() {
    this.server.registerTool(
      "get_content",
      {
        title: "Web Content Extractor",
        description: "Extract HTML content from a URL and save it to a file. Returns the extracted content including title, description, main content, and links.",
        inputSchema: {
          url: z.string().url("Must be a valid URL"),
          output_file_path: z.string().min(1, "Output file path is required")
        }
      },
      async (args) => {
        try {
          const { url, output_file_path } = GetContentArgsSchema.parse(args);

          // Fetch HTML content from URL
          const response = await fetch(url);
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }

          const html = await response.text();
          if (!html) {
            throw new Error("No HTML content received from URL");
          }

          // Extract content using web-content-extractor with fallback
          let extractedContent: string;
          try {
            extractedContent = extractContent(html);
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            console.error('Primary extraction failed:', errorMessage);
            console.error('Using fallback extraction method...');
            extractedContent = fallbackExtractContent(html);
          }

          // Prepare content to save
          const contentToSave = {
            url,
            timestamp: new Date().toISOString(),
            extractedContent: extractedContent,
            rawHtml: html
          };

          // Handle file path - ensure it's absolute and properly resolved
          let resolvedPath = output_file_path;
          if (!output_file_path.startsWith('/')) {
            // If relative path, resolve it from current working directory
            resolvedPath = path.resolve(output_file_path);
          }

          // Ensure directory exists
          const dir = dirname(resolvedPath);
          await fs.mkdir(dir, { recursive: true });

          // Save content to file
          await fs.writeFile(
            resolvedPath,
            JSON.stringify(contentToSave, null, 2),
            'utf-8'
          );

          return {
            content: [
              {
                type: "text" as const,
                text: `Successfully extracted content from ${url} and saved to ${resolvedPath}\n\n` +
                      `Extracted content length: ${extractedContent.length} characters\n\n` +
                      `Preview: ${extractedContent.substring(0, 200)}${extractedContent.length > 200 ? '...' : ''}\n\n` +
                      `Full content saved to: ${resolvedPath}`
              }
            ]
          };
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : String(error);
          return {
            content: [
              {
                type: "text" as const,
                text: `Error extracting content: ${errorMessage}`
              }
            ],
            isError: true
          };
        }
      }
    );
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Web Content Extractor MCP Server running on stdio");
  }
}

const server = new WebContentExtractorMCPServer();
server.run().catch(console.error);