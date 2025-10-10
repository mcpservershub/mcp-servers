export class CodeGenerator {
    constructor() {
        this.frameworkTemplates = {
            cypress: {
                pageObject: this.generateCypressPageObject.bind(this),
                test: this.generateCypressTest.bind(this),
                extension: 'js'
            }
        };

        this.languageExtensions = {
            javascript: 'js',
            typescript: 'ts'
        };
    }

    async generateCode(options) {
        const {
            pageAnalysis,
            patterns,
            framework,
            language,
            includePageObjects,
            includeTests,
            testTypes,
            url,
            customName
        } = options;

        const className = customName || this.generateClassName(url, pageAnalysis);
        const files = [];
        let summary = '';

        try {
            if (includePageObjects) {
                const pageObject = await this.generatePageObject({
                    pageAnalysis,
                    patterns: patterns.patterns || {},
                    framework,
                    language,
                    url,
                    customClassName: className
                });

                files.push({
                    name: `${pageObject.className}.${pageObject.fileExtension}`,
                    content: pageObject.code,
                    language: language,
                    type: 'pageObject'
                });

                summary += `✅ Page Object: ${pageObject.className}\n`;
            }

            if (includeTests) {
                for (const testType of testTypes) {
                    const testSuite = await this.generateTestSuite({
                        pageAnalysis,
                        patterns: patterns.patterns || {},
                        workflows: patterns.workflows || {},
                        framework,
                        language,
                        testType,
                        className,
                        url
                    });

                    files.push({
                        name: testSuite.fileName,
                        content: testSuite.code,
                        language: language,
                        type: 'test'
                    });

                    summary += `🧪 Test Suite: ${testSuite.suiteName} (${testType})\n`;
                }
            }

            // Generate additional configuration files if needed
            const configFiles = this.generateConfigFiles(framework, language);
            files.push(...configFiles);

            summary += `📁 Generated ${files.length} files for ${framework} framework`;

            return {
                files,
                summary,
                className,
                framework,
                language,
                patterns: patterns.patterns || {},
                workflows: patterns.workflows || {}
            };

        } catch (error) {
            throw new Error(`Code generation failed: ${error.message}`);
        }
    }

    async generatePageObject(options) {
        const { pageAnalysis, patterns, framework, language, url, customClassName } = options;

        const template = this.frameworkTemplates[framework.toLowerCase()];
        if (!template) {
            throw new Error(`Unsupported framework: ${framework}`);
        }

        const className = customClassName || this.generateClassName(url, pageAnalysis);
        const fileExtension = this.languageExtensions[language] || 'js';

        const code = await template.pageObject({
            pageAnalysis,
            patterns,
            className,
            url,
            language
        });

        return {
            className,
            code,
            fileExtension,
            framework,
            language
        };
    }

    async generateTestSuite(options) {
        const { pageAnalysis, patterns, workflows, framework, language, testType, className, url } = options;

        const template = this.frameworkTemplates[framework.toLowerCase()];
        if (!template) {
            throw new Error(`Unsupported framework: ${framework}`);
        }

        const fileExtension = this.languageExtensions[language] || 'js';
        const suiteName = `${className}${this.capitalize(testType)}Tests`;
        const fileName = `${suiteName}.${fileExtension}`;

        const code = await template.test({
            pageAnalysis,
            patterns,
            workflows,
            className,
            suiteName,
            testType,
            url,
            language
        });

        return {
            suiteName,
            fileName,
            code,
            framework,
            language,
            testType
        };
    }

    // === CYPRESS GENERATORS ===

    generateCypressPageObject({ pageAnalysis, patterns, className, url, language }) {
        const elements = this.generateElementSelectors(pageAnalysis);
        const methods = this.generateElementMethods(pageAnalysis, 'cypress');
        const workflows = this.generateWorkflowMethods(patterns, 'cypress');

        return `export class ${className} {
  // Element locators
  elements = {
${elements.map(el => `    ${el.name}: '${el.selector}',`).join('\n')}
  };

  // Navigation
  visit() {
    cy.visit('${url}');
    return this;
  }

  // Element getters
${elements.map(el => `  get ${this.capitalize(el.name)}() {
    return cy.get(this.elements.${el.name});
  }`).join('\n\n')}

  // Element actions
${methods.join('\n\n')}

  // Workflow methods
${workflows.join('\n\n')}

  // Utility methods
  waitForPageLoad() {
    cy.url().should('include', '${new URL(url).hostname}');
    return this;
  }

  verifyPageLoaded() {
    cy.title().should('not.be.empty');
    return this;
  }
}`;
    }

    generateCypressTest({ pageAnalysis, patterns, workflows, className, suiteName, testType, url }) {
        const testCases = this.generateTestCases(patterns, workflows, testType, 'cypress');

        return `import { ${className} } from '../pages/${className}';

describe('${suiteName}', () => {
  let page;

  beforeEach(() => {
    page = new ${className}();
    page.visit();
  });

${testCases.map(testCase => this.generateCypressTestCase(testCase)).join('\n\n')}

  // Cleanup
  afterEach(() => {
    // Add cleanup logic if needed
  });
});`;
    }

    generateCypressTestCase(testCase) {
        return `  describe('${testCase.category}', () => {
${testCase.tests.map(test => `    it('${test.description}', () => {
      // ${test.type} test
      ${test.steps.join('\n      ')}

      // Assertions
      ${test.assertions.join('\n      ')}
    });`).join('\n\n')}
  });`;
    }

    // === CYPRESS-SPECIFIC HELPER METHODS ===

    // === HELPER METHODS ===

    generateElementSelectors(pageAnalysis) {
        const selectors = [];

        // Buttons
        pageAnalysis.elements.buttons.forEach((button, index) => {
            const selector = this.getOptimalSelector(button);
            selectors.push({
                name: `button${button.text ? this.camelCase(button.text) : index + 1}`,
                selector: selector.value,
                locatorType: selector.type,
                value: selector.rawValue || selector.value,
                elementType: 'button'
            });
        });

        // Inputs
        pageAnalysis.elements.inputs.forEach((input, index) => {
            const selector = this.getOptimalSelector(input);
            const name = input.name || input.id || `input${this.capitalize(input.type || 'field')}${index + 1}`;
            selectors.push({
                name: this.camelCase(name),
                selector: selector.value,
                locatorType: selector.type,
                value: selector.rawValue || selector.value,
                elementType: 'input',
                inputType: input.type
            });
        });

        // Links
        pageAnalysis.elements.links.forEach((link, index) => {
            const selector = this.getOptimalSelector(link);
            const name = link.text ? this.camelCase(link.text) : `link${index + 1}`;
            selectors.push({
                name: name,
                selector: selector.value,
                locatorType: selector.type,
                value: selector.rawValue || selector.value,
                elementType: 'link'
            });
        });

        // Selects
        pageAnalysis.elements.selects.forEach((select, index) => {
            const selector = this.getOptimalSelector(select);
            const name = select.name || select.id || `select${index + 1}`;
            selectors.push({
                name: this.camelCase(name),
                selector: selector.value,
                locatorType: selector.type,
                value: selector.rawValue || selector.value,
                elementType: 'select'
            });
        });

        return selectors;
    }

    getOptimalSelector(element) {
        // Priority: data-testid > id > name > class > text > css
        if (element.dataTestId) {
            return {
                type: 'css',
                value: `[data-testid="${element.dataTestId}"]`,
                rawValue: element.dataTestId
            };
        }

        if (element.id) {
            return {
                type: 'id',
                value: `#${element.id}`,
                rawValue: element.id
            };
        }

        if (element.name) {
            return {
                type: 'css',
                value: `[name="${element.name}"]`,
                rawValue: element.name
            };
        }

        if (element.className && element.className.split(' ').length === 1) {
            return {
                type: 'css',
                value: `.${element.className}`,
                rawValue: element.className
            };
        }

        if (element.text && element.text.length < 50) {
            return {
                type: 'xpath',
                value: `//*[contains(text(), "${element.text}")]`,
                rawValue: element.text
            };
        }

        // Fallback to tag name
        const tagName = element.tagName?.toLowerCase() || 'div';
        return {
            type: 'css',
            value: tagName,
            rawValue: tagName
        };
    }

    generateElementMethods(pageAnalysis, framework = 'cypress') {
        const methods = [];
        const elements = this.generateElementSelectors(pageAnalysis);

        elements.forEach(element => {
            switch (element.elementType) {
                case 'button':
                case 'link':
                    methods.push(this.generateCypressClickMethod(element));
                    break;
                case 'input':
                    if (element.inputType === 'checkbox' || element.inputType === 'radio') {
                        methods.push(this.generateCypressCheckMethod(element));
                    } else if (element.inputType === 'file') {
                        methods.push(this.generateCypressFileUploadMethod(element));
                    } else {
                        methods.push(this.generateCypressTypeMethod(element));
                    }
                    break;
                case 'select':
                    methods.push(this.generateCypressSelectMethod(element));
                    break;
            }
        });

        return methods;
    }

    generateCypressClickMethod(element) {
        const methodName = `click${this.capitalize(element.name)}`;
        return `  ${methodName}() {
    this.${this.capitalize(element.name)}.click();
    return this;
  }`;
    }

    generateCypressTypeMethod(element) {
        const methodName = `type${this.capitalize(element.name)}`;
        return `  ${methodName}(text) {
    this.${this.capitalize(element.name)}.clear().type(text);
    return this;
  }`;
    }

    generateCypressCheckMethod(element) {
        const methodName = `check${this.capitalize(element.name)}`;
        return `  ${methodName}() {
    this.${this.capitalize(element.name)}.check();
    return this;
  }`;
    }

    generateCypressSelectMethod(element) {
        const methodName = `select${this.capitalize(element.name)}`;
        return `  ${methodName}(value) {
    this.${this.capitalize(element.name)}.select(value);
    return this;
  }`;
    }

    generateCypressFileUploadMethod(element) {
        const methodName = `upload${this.capitalize(element.name)}`;
        return `  ${methodName}(filePath) {
    this.${this.capitalize(element.name)}.selectFile(filePath);
    return this;
  }`;
    }

    generateWorkflowMethods(patterns, framework = 'cypress') {
        const methods = [];

        Object.entries(patterns).forEach(([patternName, pattern]) => {
            if (pattern.detected && pattern.elements) {
                switch (patternName) {
                    case 'login':
                        methods.push(this.generateCypressLoginWorkflow(pattern.elements));
                        break;
                    case 'search':
                        methods.push(this.generateCypressSearchWorkflow(pattern.elements));
                        break;
                    case 'registration':
                        methods.push(this.generateCypressRegistrationWorkflow(pattern.elements));
                        break;
                }
            }
        });

        return methods;
    }

    generateCypressLoginWorkflow(elements) {
        return `  login(username, password) {
    if (username) this.typeUsernameField(username);
    if (password) this.typePasswordField(password);
    this.clickSubmitButton();
    return this;
  }`;
    }

    generateCypressSearchWorkflow(elements) {
        return `  search(query) {
    this.typeSearchInput(query);
    if (this.searchButton) this.clickSearchButton();
    return this;
  }`;
    }

    generateCypressRegistrationWorkflow(elements) {
        return `  register(userData) {
    if (userData.email) this.typeEmailField(userData.email);
    if (userData.password) this.typePasswordField(userData.password);
    if (userData.confirmPassword) this.typeConfirmPasswordField(userData.confirmPassword);
    if (userData.firstName) this.typeFirstNameField(userData.firstName);
    if (userData.lastName) this.typeLastNameField(userData.lastName);
    this.clickSubmitButton();
    return this;
  }`;
    }

    generateTestCases(patterns, workflows, testType, framework) {
        const testCases = [];

        // Generate test cases based on detected patterns
        Object.entries(patterns).forEach(([patternName, pattern]) => {
            if (pattern.detected && pattern.testCases) {
                testCases.push({
                    category: this.capitalize(patternName),
                    tests: this.generatePatternTests(pattern, testType, framework)
                });
            }
        });

        // Generate workflow tests
        Object.entries(workflows).forEach(([workflowName, workflow]) => {
            testCases.push({
                category: workflow.name,
                tests: this.generateWorkflowTests(workflow, testType, framework)
            });
        });

        // Add general test cases
        testCases.push({
            category: 'General',
            tests: this.generateGeneralTests(testType, framework)
        });

        return testCases;
    }

    generatePatternTests(pattern, testType, framework) {
        const tests = [];

        pattern.testCases.forEach(testCaseName => {
            const test = {
                description: testCaseName.toLowerCase(),
                type: testType,
                steps: this.generateTestSteps(testCaseName, pattern, framework),
                assertions: this.generateAssertions(testCaseName, pattern, framework)
            };
            tests.push(test);
        });

        return tests;
    }

    generateWorkflowTests(workflow, testType, framework) {
        return [{
            description: `complete ${workflow.name.toLowerCase()} workflow`,
            type: testType,
            steps: [`// Complete ${workflow.name} workflow`, ...workflow.steps.map(step => `// ${step}`)],
            assertions: [`// Verify workflow completion`]
        }];
    }

    generateGeneralTests(testType, framework) {
        const tests = [
            {
                description: 'page loads successfully',
                type: 'smoke',
                steps: ['// Verify page loads'],
                assertions: ['// Assert page title and URL']
            },
            {
                description: 'page is responsive',
                type: 'ui',
                steps: ['// Test different viewport sizes'],
                assertions: ['// Assert responsive layout']
            }
        ];

        if (testType === 'accessibility') {
            tests.push({
                description: 'page meets accessibility standards',
                type: 'accessibility',
                steps: ['// Run accessibility audit'],
                assertions: ['// Assert no accessibility violations']
            });
        }

        return tests;
    }

    generateTestSteps(testCaseName, pattern, framework) {
        // Generate framework-specific test steps based on test case name
        const steps = [];

        if (testCaseName.includes('login')) {
            steps.push("await page.login('testuser', 'testpass');");
        } else if (testCaseName.includes('search')) {
            steps.push("await page.search('test query');");
        } else {
            steps.push("// Add test implementation");
        }

        return steps;
    }

    generateAssertions(testCaseName, pattern, framework) {
        const assertions = [];

        switch (framework) {
            case 'cypress':
                assertions.push("cy.url().should('not.include', 'error');");
                break;
            case 'selenium':
                assertions.push("expect(await page.getCurrentUrl()).not.toContain('error');");
                break;
            case 'playwright':
                assertions.push("await expect(page.locator('body')).toBeVisible();");
                break;
            case 'puppeteer':
                assertions.push("expect(await page.url()).not.toContain('error');");
                break;
        }

        return assertions;
    }

    generateConfigFiles(framework = 'cypress', language = 'javascript') {
        const configFiles = [];

        configFiles.push({
            name: language === 'typescript' ? 'cypress.config.ts' : 'cypress.config.js',
            content: this.generateCypressConfig(language),
            language: language,
            type: 'config'
        });

        return configFiles;
    }

    generateCypressConfig(language = 'javascript') {
        if (language === 'typescript') {
            return `import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    viewportWidth: 1920,
    viewportHeight: 1080,
    video: true,
    screenshotOnRunFailure: true,
    defaultCommandTimeout: 10000,
    pageLoadTimeout: 30000,
    requestTimeout: 10000,
    responseTimeout: 30000,
    supportFile: 'cypress/support/e2e.ts',
    specPattern: 'cypress/e2e/**/*.cy.ts',
    setupNodeEvents(on: Cypress.PluginEvents, config: Cypress.PluginConfigOptions) {
      // implement node event listeners here
      return config;
    },
  },
});`;
        }

        return `import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    viewportWidth: 1920,
    viewportHeight: 1080,
    video: true,
    screenshotOnRunFailure: true,
    defaultCommandTimeout: 10000,
    pageLoadTimeout: 30000,
    requestTimeout: 10000,
    responseTimeout: 30000,
    supportFile: 'cypress/support/e2e.js',
    specPattern: 'cypress/e2e/**/*.cy.js',
    setupNodeEvents(on, config) {
      // implement node event listeners here
      return config;
    },
  },
});`;
    }

    // Utility methods
    generateClassName(url, pageAnalysis) {
        try {
            const urlObj = new URL(url);
            let name = urlObj.hostname.replace(/[^a-zA-Z0-9]/g, '');

            if (urlObj.pathname && urlObj.pathname !== '/') {
                const pathParts = urlObj.pathname.split('/').filter(Boolean);
                name += pathParts.map(part => this.capitalize(part.replace(/[^a-zA-Z0-9]/g, ''))).join('');
            }

            return this.capitalize(name) + 'Page';
        } catch {
            return 'GenericPage';
        }
    }

    camelCase(str) {
        return str.replace(/[^a-zA-Z0-9]/g, ' ')
                 .split(' ')
                 .filter(word => word.length > 0)
                 .map((word, index) => index === 0 ? word.toLowerCase() : this.capitalize(word))
                 .join('');
    }

    capitalize(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
    }
}