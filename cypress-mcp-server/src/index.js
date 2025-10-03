#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import { CodeGenerator } from "./code-generator.js";
import { FileManager } from "./file-manager.js";
import { ElementAnalyzer } from "./element-analyzer.js";
import { TestPatternDetector } from "./test-pattern-detector.js";

// Create the MCP server
const server = new McpServer({
    name: "Enhanced Cypress MCP Server",
    version: "1.0.0"
});

// Global instances
const codeGenerator = new CodeGenerator();
const fileManager = new FileManager();
const elementAnalyzer = new ElementAnalyzer();
const testPatternDetector = new TestPatternDetector();

// ===== CYPRESS CODE GENERATION TOOLS =====

server.tool(
    "analyzePageAndGenerateCypress",
    "Analyze a web page and generate comprehensive Cypress test code",
    {
        url: z.string().describe("URL to analyze"),
        language: z.enum(["javascript", "typescript"]).default("javascript").describe("Programming language"),
        includePageObjects: z.boolean().default(true).describe("Generate Page Object Model classes"),
        includeTests: z.boolean().default(true).describe("Generate test suites"),
        testTypes: z.array(z.enum(["unit", "integration", "e2e", "accessibility", "performance"])).default(["e2e"]).describe("Types of tests to generate")
    },
    async ({ url, language, includePageObjects, includeTests, testTypes }) => {
        try {
            // Analyze the page using Puppeteer
            const pageAnalysis = await elementAnalyzer.analyzePage(url);

            // Detect test patterns and workflows
            const patterns = await testPatternDetector.detectPatterns(pageAnalysis);

            // Generate code based on analysis
            const generatedCode = await codeGenerator.generateCode({
                pageAnalysis,
                patterns,
                framework: 'cypress',
                language,
                includePageObjects,
                includeTests,
                testTypes,
                url
            });

            return {
                content: [{
                    type: "text",
                    text: `✅ Cypress code generated successfully!\n\n${generatedCode.summary}\n\n${generatedCode.files.map(f => `📄 ${f.name}:\n\`\`\`${f.language}\n${f.content}\n\`\`\``).join('\n\n')}`
                }]
            };
        } catch (error) {
            return {
                content: [{
                    type: "text",
                    text: `❌ Cypress code generation failed: ${error.message}`
                }]
            };
        }
    }
);

server.tool(
    "createCypressFiles",
    "Create Cypress test files directly in a Cypress project directory",
    {
        url: z.string().describe("URL to analyze"),
        projectPath: z.string().optional().describe("Project directory path (auto-detected if not provided)"),
        language: z.enum(["javascript", "typescript"]).default("javascript").describe("Programming language"),
        pageObjectName: z.string().optional().describe("Custom name for page object class")
    },
    async ({ url, projectPath, language, pageObjectName }) => {
        try {
            // Detect project structure
            const detectedProject = await fileManager.detectProjectStructure(projectPath);

            // Validate Cypress project
            const validation = await fileManager.validateCypressProject(detectedProject.projectRoot);
            if (!validation.valid) {
                return {
                    content: [{
                        type: "text",
                        text: `❌ Invalid Cypress project:\n${validation.issues.join('\n')}\n\nPlease ensure you're in a valid Cypress project directory.`
                    }]
                };
            }

            // Analyze the page
            const pageAnalysis = await elementAnalyzer.analyzePage(url);
            const patterns = await testPatternDetector.detectPatterns(pageAnalysis);

            // Generate code
            const generatedCode = await codeGenerator.generateCode({
                pageAnalysis,
                patterns,
                framework: 'cypress',
                language,
                includePageObjects: true,
                includeTests: true,
                testTypes: ["e2e"],
                url,
                customName: pageObjectName
            });

            // Create files in project
            const createdFiles = await fileManager.createProjectFiles(
                detectedProject.projectRoot,
                generatedCode,
                'cypress',
                language
            );

            return {
                content: [{
                    type: "text",
                    text: `✅ Cypress files created successfully!\n\nProject: ${detectedProject.projectType.join(', ')}\nRoot: ${detectedProject.projectRoot}\n\n📁 Created Files:\n${createdFiles.map(f => `  • ${f.relativePath}`).join('\n')}\n\n🚀 Next Steps:\n${detectedProject.nextSteps.join('\n• ')}`
                }]
            };
        } catch (error) {
            return {
                content: [{
                    type: "text",
                    text: `❌ Cypress file creation failed: ${error.message}`
                }]
            };
        }
    }
);

server.tool(
    "generateCypressPageObject",
    "Generate Cypress Page Object Model class for a specific URL",
    {
        url: z.string().describe("URL to analyze"),
        className: z.string().optional().describe("Custom class name"),
        language: z.enum(["javascript", "typescript"]).default("javascript").describe("Programming language"),
        includeWorkflows: z.boolean().default(true).describe("Include workflow methods (login, search, etc.)")
    },
    async ({ url, className, language, includeWorkflows }) => {
        try {
            const pageAnalysis = await elementAnalyzer.analyzePage(url);
            const patterns = includeWorkflows ? await testPatternDetector.detectPatterns(pageAnalysis) : {};

            const pageObject = await codeGenerator.generatePageObject({
                pageAnalysis,
                patterns: patterns.patterns || {},
                framework: 'cypress',
                language,
                url,
                customClassName: className
            });

            return {
                content: [{
                    type: "text",
                    text: `✅ Cypress Page Object generated!\n\n📄 ${pageObject.className}.${pageObject.fileExtension}:\n\`\`\`${language}\n${pageObject.code}\n\`\`\``
                }]
            };
        } catch (error) {
            return {
                content: [{
                    type: "text",
                    text: `❌ Cypress Page Object generation failed: ${error.message}`
                }]
            };
        }
    }
);

// ===== UTILITY TOOLS =====

server.tool(
    "analyzeElement",
    "Analyze a specific element on a page",
    {
        url: z.string().describe("URL to analyze"),
        selector: z.string().describe("CSS selector for the element"),
        includeContext: z.boolean().default(true).describe("Include surrounding context")
    },
    async ({ url, selector, includeContext }) => {
        try {
            const elementInfo = await elementAnalyzer.analyzeElement(url, selector, includeContext);

            return {
                content: [{
                    type: "text",
                    text: `🔍 Element Analysis:\n\n${JSON.stringify(elementInfo, null, 2)}`
                }]
            };
        } catch (error) {
            return {
                content: [{
                    type: "text",
                    text: `❌ Element analysis failed: ${error.message}`
                }]
            };
        }
    }
);

server.tool(
    "detectTestPatterns",
    "Detect test patterns and workflows on a page",
    {
        url: z.string().describe("URL to analyze")
    },
    async ({ url }) => {
        try {
            const pageAnalysis = await elementAnalyzer.analyzePage(url);
            const patterns = await testPatternDetector.detectPatterns(pageAnalysis);

            return {
                content: [{
                    type: "text",
                    text: `🎯 Detected Patterns:\n\n${JSON.stringify(patterns, null, 2)}`
                }]
            };
        } catch (error) {
            return {
                content: [{
                    type: "text",
                    text: `❌ Pattern detection failed: ${error.message}`
                }]
            };
        }
    }
);

// Create transport and start server
const transport = new StdioServerTransport();

// Start the server
(async () => {
    try {
        await server.connect(transport);
        console.error("Enhanced Cypress MCP Server started successfully");
    } catch (error) {
        console.error("Failed to start server:", error);
        process.exit(1);
    }
})();

// Graceful shutdown
process.on('SIGINT', async () => {
    console.error("Shutting down Cypress MCP server...");
    await elementAnalyzer.closeBrowser();
    process.exit(0);
});

process.on('SIGTERM', async () => {
    console.error("Shutting down Cypress MCP server...");
    await elementAnalyzer.closeBrowser();
    process.exit(0);
});