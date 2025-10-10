import fs from 'fs-extra';
import path from 'path';

export class FileManager {
    constructor() {
        this.supportedProjects = {
            cypress: {
                configFiles: ['cypress.config.js', 'cypress.config.ts', 'cypress.json'],
                directories: ['cypress', 'cypress/e2e', 'cypress/support', 'cypress/fixtures'],
                pageObjectPath: 'cypress/support/pages',
                testPath: 'cypress/e2e'
            }
        };
    }

    async detectProjectStructure(startPath = process.cwd()) {
        const projectRoot = await this.findProjectRoot(startPath);
        const projectType = await this.detectProjectType(projectRoot);
        const packageJson = await this.readPackageJson(projectRoot);

        return {
            projectRoot,
            projectType,
            packageJson,
            supportedFrameworks: this.getSupportedFrameworks(packageJson),
            nextSteps: this.generateNextSteps(projectType, packageJson)
        };
    }

    async findProjectRoot(startPath) {
        let currentPath = startPath;
        const root = path.parse(currentPath).root;

        while (currentPath !== root) {
            // Check for package.json (Node.js project)
            const packageJsonPath = path.join(currentPath, 'package.json');
            if (await fs.pathExists(packageJsonPath)) {
                return currentPath;
            }

            // Check for Cypress config files
            const cypressConfigs = ['cypress.config.js', 'cypress.config.ts', 'cypress.json'];
            for (const config of cypressConfigs) {
                if (await fs.pathExists(path.join(currentPath, config))) {
                    return currentPath;
                }
            }

            currentPath = path.dirname(currentPath);
        }

        // If no project root found, use the start path
        return startPath;
    }

    async detectProjectType(projectRoot) {
        const detectedTypes = [];

        // Check for Cypress config files
        const cypressConfig = this.supportedProjects.cypress;
        for (const configFile of cypressConfig.configFiles) {
            if (await fs.pathExists(path.join(projectRoot, configFile))) {
                detectedTypes.push('cypress');
                break;
            }
        }

        // Check package.json dependencies
        const packageJson = await this.readPackageJson(projectRoot);
        if (packageJson) {
            const allDeps = {
                ...packageJson.dependencies,
                ...packageJson.devDependencies
            };

            if (allDeps.cypress) detectedTypes.push('cypress');
        }

        return detectedTypes.length > 0 ? detectedTypes : ['cypress']; // Default to cypress
    }

    async readPackageJson(projectRoot) {
        const packageJsonPath = path.join(projectRoot, 'package.json');
        try {
            if (await fs.pathExists(packageJsonPath)) {
                return await fs.readJson(packageJsonPath);
            }
        } catch (error) {
            console.warn(`Could not read package.json: ${error.message}`);
        }
        return null;
    }

    getSupportedFrameworks(packageJson) {
        if (!packageJson) return ['cypress'];

        const allDeps = {
            ...packageJson.dependencies,
            ...packageJson.devDependencies
        };

        const frameworks = [];
        if (allDeps.cypress) frameworks.push('cypress');

        return frameworks.length > 0 ? frameworks : ['cypress'];
    }

    async createProjectFiles(projectRoot, generatedCode, framework = 'cypress', language = 'javascript') {
        const projectConfig = this.supportedProjects.cypress;
        const createdFiles = [];

        try {
            // Ensure project directories exist
            await this.ensureDirectoryStructure(projectRoot, projectConfig);

            // Create page object files
            const pageObjectFiles = generatedCode.files.filter(f => f.type === 'pageObject');
            for (const file of pageObjectFiles) {
                const filePath = await this.createPageObjectFile(projectRoot, file, projectConfig);
                createdFiles.push({
                    absolutePath: filePath,
                    relativePath: path.relative(projectRoot, filePath),
                    type: 'pageObject'
                });
            }

            // Create test files
            const testFiles = generatedCode.files.filter(f => f.type === 'test');
            for (const file of testFiles) {
                const filePath = await this.createTestFile(projectRoot, file, projectConfig);
                createdFiles.push({
                    absolutePath: filePath,
                    relativePath: path.relative(projectRoot, filePath),
                    type: 'test'
                });
            }

            // Create config files
            const configFiles = generatedCode.files.filter(f => f.type === 'config');
            for (const file of configFiles) {
                const filePath = await this.createConfigFile(projectRoot, file);
                createdFiles.push({
                    absolutePath: filePath,
                    relativePath: path.relative(projectRoot, filePath),
                    type: 'config'
                });
            }

            // Update or create index files
            await this.updateIndexFiles(projectRoot, projectConfig, pageObjectFiles);

            return createdFiles;

        } catch (error) {
            throw new Error(`Failed to create Cypress project files: ${error.message}`);
        }
    }

    async ensureDirectoryStructure(projectRoot, projectConfig) {
        const directories = [
            path.join(projectRoot, projectConfig.pageObjectPath),
            path.join(projectRoot, projectConfig.testPath),
            ...projectConfig.directories.map(dir => path.join(projectRoot, dir))
        ];

        for (const dir of directories) {
            await fs.ensureDir(dir);
        }
    }

    async createPageObjectFile(projectRoot, file, projectConfig) {
        const fileName = this.sanitizeFileName(file.name);
        const filePath = path.join(projectRoot, projectConfig.pageObjectPath, fileName);

        // Check if file exists and create backup
        if (await fs.pathExists(filePath)) {
            const backupPath = await this.createBackup(filePath);
            console.log(`Page object backup created: ${backupPath}`);
        }

        await fs.writeFile(filePath, file.content, 'utf8');
        return filePath;
    }

    async createTestFile(projectRoot, file, projectConfig) {
        const fileName = this.sanitizeFileName(file.name);
        const filePath = path.join(projectRoot, projectConfig.testPath, fileName);

        // Check if file exists and create backup
        if (await fs.pathExists(filePath)) {
            const backupPath = await this.createBackup(filePath);
            console.log(`Test file backup created: ${backupPath}`);
        }

        await fs.writeFile(filePath, file.content, 'utf8');
        return filePath;
    }

    async createConfigFile(projectRoot, file) {
        const fileName = this.sanitizeFileName(file.name);
        const filePath = path.join(projectRoot, fileName);

        // Config files are more sensitive, create backup before overwriting
        if (await fs.pathExists(filePath)) {
            const backupPath = await this.createBackup(filePath);
            console.log(`Config backup created: ${backupPath}`);
        }

        await fs.writeFile(filePath, file.content, 'utf8');
        return filePath;
    }

    async createBackup(filePath) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const ext = path.extname(filePath);
        const basename = path.basename(filePath, ext);
        const dirname = path.dirname(filePath);

        const backupPath = path.join(dirname, `${basename}.backup.${timestamp}${ext}`);
        await fs.copy(filePath, backupPath);
        return backupPath;
    }

    async updateIndexFiles(projectRoot, projectConfig, pageObjectFiles) {
        try {
            const indexPath = path.join(projectRoot, projectConfig.pageObjectPath, 'index.js');

            // Get all page object files in the directory
            const pagesDir = path.join(projectRoot, projectConfig.pageObjectPath);
            const existingFiles = await fs.readdir(pagesDir);
            const jsFiles = existingFiles.filter(file =>
                (file.endsWith('.js') || file.endsWith('.ts')) &&
                file !== 'index.js' &&
                file !== 'index.ts' &&
                !file.includes('.backup.')
            );

            // Generate exports for all page object files
            const exports = jsFiles.map(file => {
                const className = this.extractClassNameFromFile(file);
                const modulePath = `./${path.basename(file, path.extname(file))}`;
                return `export { ${className} } from '${modulePath}';`;
            });

            const indexContent = `// Auto-generated index file for Cypress page objects
// Generated on: ${new Date().toISOString()}

${exports.join('\n')}
`;

            await fs.writeFile(indexPath, indexContent, 'utf8');
        } catch (error) {
            console.warn(`Could not update index file: ${error.message}`);
        }
    }

    extractClassNameFromFile(fileName) {
        // Try to extract class name from file name
        const baseName = path.basename(fileName, path.extname(fileName));

        // Convert kebab-case or snake_case to PascalCase
        const className = baseName
            .split(/[-_]/)
            .map(part => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
            .join('');

        return className || 'UnknownPage';
    }

    sanitizeFileName(fileName) {
        // Replace invalid characters and ensure proper extension
        return fileName.replace(/[<>:"/\\|?*]/g, '_').replace(/\s+/g, '_');
    }

    generateNextSteps(projectTypes, packageJson) {
        const steps = [
            '🚀 Run: npm run cy:open or npx cypress open',
            '📝 Import page objects in your test files',
            '🧪 Customize generated test cases as needed',
            '✅ Add proper assertions and validations',
            '🔧 Configure Cypress settings in cypress.config.js',
            '📊 Consider adding data-testid attributes to elements',
            '🚀 Set up CI/CD integration for automated testing'
        ];

        return steps;
    }

    async validateCypressProject(projectRoot) {
        const projectConfig = this.supportedProjects.cypress;
        const issues = [];

        // Check if required directories exist
        for (const dir of projectConfig.directories) {
            const dirPath = path.join(projectRoot, dir);
            if (!(await fs.pathExists(dirPath))) {
                issues.push(`Missing Cypress directory: ${dir}`);
            }
        }

        // Check for config files
        let hasConfig = false;
        for (const configFile of projectConfig.configFiles) {
            if (await fs.pathExists(path.join(projectRoot, configFile))) {
                hasConfig = true;
                break;
            }
        }

        if (!hasConfig) {
            issues.push(`No Cypress configuration file found. Expected one of: ${projectConfig.configFiles.join(', ')}`);
        }

        // Check package.json for Cypress
        const packageJson = await this.readPackageJson(projectRoot);
        if (packageJson) {
            const allDeps = { ...packageJson.dependencies, ...packageJson.devDependencies };
            if (!allDeps.cypress) {
                issues.push('Cypress not found in package.json dependencies');
            }
        }

        return {
            valid: issues.length === 0,
            issues
        };
    }

    async getCypressProjectStats(projectRoot) {
        const stats = {
            totalFiles: 0,
            pageObjects: 0,
            tests: 0,
            fixtures: 0,
            supportFiles: 0
        };

        try {
            const cypressDir = path.join(projectRoot, 'cypress');
            if (!(await fs.pathExists(cypressDir))) {
                return stats;
            }

            const walk = async (dir, category = '') => {
                const items = await fs.readdir(dir);

                for (const item of items) {
                    const fullPath = path.join(dir, item);
                    const stat = await fs.stat(fullPath);

                    if (stat.isDirectory()) {
                        let newCategory = category;
                        if (item === 'e2e') newCategory = 'tests';
                        else if (item === 'support') newCategory = 'support';
                        else if (item === 'fixtures') newCategory = 'fixtures';
                        else if (item === 'pages') newCategory = 'pages';

                        await walk(fullPath, newCategory);
                    } else if (stat.isFile() && (item.endsWith('.js') || item.endsWith('.ts'))) {
                        stats.totalFiles++;

                        if (category === 'tests' || item.includes('.cy.')) {
                            stats.tests++;
                        } else if (category === 'pages' || item.includes('Page') || item.includes('page')) {
                            stats.pageObjects++;
                        } else if (category === 'fixtures') {
                            stats.fixtures++;
                        } else if (category === 'support') {
                            stats.supportFiles++;
                        }
                    }
                }
            };

            await walk(cypressDir);
        } catch (error) {
            console.warn(`Could not get Cypress project stats: ${error.message}`);
        }

        return stats;
    }

    async cleanupOldBackups(projectRoot, olderThanDays = 30) {
        const cutoffTime = Date.now() - (olderThanDays * 24 * 60 * 60 * 1000);
        const cleanedFiles = [];

        const walk = async (dir) => {
            try {
                const items = await fs.readdir(dir);

                for (const item of items) {
                    const fullPath = path.join(dir, item);
                    const stat = await fs.stat(fullPath);

                    if (stat.isFile() && item.includes('.backup.')) {
                        if (stat.mtime.getTime() < cutoffTime) {
                            await fs.remove(fullPath);
                            cleanedFiles.push(path.relative(projectRoot, fullPath));
                        }
                    } else if (stat.isDirectory()) {
                        await walk(fullPath);
                    }
                }
            } catch (error) {
                console.warn(`Could not clean directory ${dir}: ${error.message}`);
            }
        };

        await walk(projectRoot);
        return cleanedFiles;
    }
}