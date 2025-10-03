export class TestPatternDetector {
    constructor() {
        this.patterns = {
            login: this.detectLoginPattern.bind(this),
            search: this.detectSearchPattern.bind(this),
            registration: this.detectRegistrationPattern.bind(this),
            checkout: this.detectCheckoutPattern.bind(this),
            navigation: this.detectNavigationPattern.bind(this),
            crud: this.detectCrudPattern.bind(this),
            modal: this.detectModalPattern.bind(this),
            pagination: this.detectPaginationPattern.bind(this),
            filters: this.detectFiltersPattern.bind(this),
            fileUpload: this.detectFileUploadPattern.bind(this),
            formValidation: this.detectFormValidationPattern.bind(this),
            dataTable: this.detectDataTablePattern.bind(this)
        };
    }

    async detectPatterns(pageAnalysis) {
        const detectedPatterns = {};

        for (const [patternName, detector] of Object.entries(this.patterns)) {
            try {
                const pattern = await detector(pageAnalysis);
                if (pattern.detected) {
                    detectedPatterns[patternName] = pattern;
                }
            } catch (error) {
                console.warn(`Pattern detection failed for ${patternName}:`, error.message);
            }
        }

        // Detect complex workflows based on multiple patterns
        const workflows = this.detectWorkflows(detectedPatterns, pageAnalysis);

        return {
            patterns: detectedPatterns,
            workflows,
            summary: this.generatePatternSummary(detectedPatterns, workflows)
        };
    }

    detectLoginPattern(pageAnalysis) {
        const { elements, forms } = pageAnalysis;

        const hasPassword = elements.inputs.some(input =>
            input.type === 'password'
        );

        const hasUsernameField = elements.inputs.some(input =>
            input.type === 'email' ||
            input.name?.toLowerCase().includes('user') ||
            input.name?.toLowerCase().includes('login') ||
            input.name?.toLowerCase().includes('email') ||
            input.placeholder?.toLowerCase().includes('email') ||
            input.placeholder?.toLowerCase().includes('username')
        );

        const hasSubmitButton = elements.buttons.some(button =>
            button.type === 'submit' ||
            button.text?.toLowerCase().includes('login') ||
            button.text?.toLowerCase().includes('sign in') ||
            button.text?.toLowerCase().includes('log in')
        );

        const loginForm = forms.forms.find(form =>
            form.elements.some(el => el.type === 'password')
        );

        const detected = hasPassword && hasUsernameField && hasSubmitButton;

        return {
            detected,
            confidence: detected ? this.calculateConfidence([hasPassword, hasUsernameField, hasSubmitButton]) : 0,
            elements: detected ? {
                usernameField: elements.inputs.find(input =>
                    input.type === 'email' ||
                    input.name?.toLowerCase().includes('user') ||
                    input.name?.toLowerCase().includes('email')
                ),
                passwordField: elements.inputs.find(input => input.type === 'password'),
                submitButton: elements.buttons.find(button =>
                    button.type === 'submit' ||
                    button.text?.toLowerCase().includes('login')
                ),
                form: loginForm
            } : null,
            testCases: detected ? [
                'Valid credentials login',
                'Invalid credentials error',
                'Empty username validation',
                'Empty password validation',
                'Remember me functionality',
                'Forgot password link',
                'Password visibility toggle'
            ] : []
        };
    }

    detectSearchPattern(pageAnalysis) {
        const { elements } = pageAnalysis;

        const searchInputs = elements.inputs.filter(input =>
            input.type === 'search' ||
            input.name?.toLowerCase().includes('search') ||
            input.name?.toLowerCase().includes('query') ||
            input.placeholder?.toLowerCase().includes('search') ||
            input.id?.toLowerCase().includes('search')
        );

        const searchButtons = elements.buttons.filter(button =>
            button.text?.toLowerCase().includes('search') ||
            button.text?.toLowerCase().includes('find') ||
            button.id?.toLowerCase().includes('search')
        );

        const detected = searchInputs.length > 0;

        return {
            detected,
            confidence: detected ? this.calculateConfidence([
                searchInputs.length > 0,
                searchButtons.length > 0,
                pageAnalysis.url.includes('search')
            ]) : 0,
            elements: detected ? {
                searchInput: searchInputs[0],
                searchButton: searchButtons[0] || elements.buttons.find(btn => btn.type === 'submit'),
                filters: this.detectSearchFilters(elements),
                sorting: this.detectSortingOptions(elements)
            } : null,
            testCases: detected ? [
                'Valid search query',
                'Empty search query',
                'Special characters in search',
                'Long search query',
                'No results scenario',
                'Search suggestions/autocomplete',
                'Search filters application',
                'Search result sorting'
            ] : []
        };
    }

    detectRegistrationPattern(pageAnalysis) {
        const { elements, forms } = pageAnalysis;

        const registrationForm = forms.forms.find(form =>
            form.elements.length > 3 && // Registration forms typically have multiple fields
            form.elements.some(el => el.type === 'password')
        );

        const hasMultipleInputs = elements.inputs.length > 3;
        const hasEmailField = elements.inputs.some(input =>
            input.type === 'email' ||
            input.name?.toLowerCase().includes('email')
        );
        const hasPasswordField = elements.inputs.some(input => input.type === 'password');
        const hasConfirmPassword = elements.inputs.filter(input => input.type === 'password').length > 1;

        const registrationKeywords = ['register', 'signup', 'sign up', 'create account', 'join'];
        const hasRegistrationText = elements.buttons.some(button =>
            registrationKeywords.some(keyword =>
                button.text?.toLowerCase().includes(keyword)
            )
        ) || registrationKeywords.some(keyword =>
            pageAnalysis.title?.toLowerCase().includes(keyword) ||
            pageAnalysis.url.toLowerCase().includes(keyword)
        );

        const detected = hasMultipleInputs && hasEmailField && hasPasswordField && hasRegistrationText;

        return {
            detected,
            confidence: detected ? this.calculateConfidence([
                hasMultipleInputs,
                hasEmailField,
                hasPasswordField,
                hasConfirmPassword,
                hasRegistrationText
            ]) : 0,
            elements: detected ? {
                form: registrationForm,
                emailField: elements.inputs.find(input =>
                    input.type === 'email' || input.name?.toLowerCase().includes('email')
                ),
                passwordFields: elements.inputs.filter(input => input.type === 'password'),
                submitButton: elements.buttons.find(button =>
                    registrationKeywords.some(keyword =>
                        button.text?.toLowerCase().includes(keyword)
                    )
                ),
                requiredFields: elements.inputs.filter(input => input.required),
                termsCheckbox: elements.inputs.find(input =>
                    input.type === 'checkbox' &&
                    (input.name?.toLowerCase().includes('terms') ||
                     input.name?.toLowerCase().includes('agree'))
                )
            } : null,
            testCases: detected ? [
                'Valid registration data',
                'Email format validation',
                'Password strength validation',
                'Confirm password matching',
                'Required field validation',
                'Terms and conditions acceptance',
                'Duplicate email handling',
                'Username availability check'
            ] : []
        };
    }

    detectCheckoutPattern(pageAnalysis) {
        const { elements } = pageAnalysis;

        const checkoutKeywords = ['checkout', 'payment', 'billing', 'shipping', 'cart', 'order'];
        const hasCheckoutKeywords = checkoutKeywords.some(keyword =>
            pageAnalysis.title?.toLowerCase().includes(keyword) ||
            pageAnalysis.url.toLowerCase().includes(keyword)
        );

        const hasCreditCardInputs = elements.inputs.some(input =>
            input.name?.toLowerCase().includes('card') ||
            input.name?.toLowerCase().includes('credit') ||
            input.placeholder?.toLowerCase().includes('card number')
        );

        const hasShippingInputs = elements.inputs.some(input =>
            input.name?.toLowerCase().includes('address') ||
            input.name?.toLowerCase().includes('shipping') ||
            input.name?.toLowerCase().includes('zip') ||
            input.name?.toLowerCase().includes('postal')
        );

        const hasOrderTotal = pageAnalysis.semantics.headings.some(heading =>
            heading.text.toLowerCase().includes('total') ||
            heading.text.includes('$') ||
            heading.text.includes('€') ||
            heading.text.includes('£')
        );

        const detected = hasCheckoutKeywords && (hasCreditCardInputs || hasShippingInputs);

        return {
            detected,
            confidence: detected ? this.calculateConfidence([
                hasCheckoutKeywords,
                hasCreditCardInputs,
                hasShippingInputs,
                hasOrderTotal
            ]) : 0,
            elements: detected ? {
                paymentFields: elements.inputs.filter(input =>
                    input.name?.toLowerCase().includes('card') ||
                    input.name?.toLowerCase().includes('payment')
                ),
                shippingFields: elements.inputs.filter(input =>
                    input.name?.toLowerCase().includes('address') ||
                    input.name?.toLowerCase().includes('shipping')
                ),
                submitButton: elements.buttons.find(button =>
                    button.text?.toLowerCase().includes('place order') ||
                    button.text?.toLowerCase().includes('complete') ||
                    button.text?.toLowerCase().includes('pay')
                )
            } : null,
            testCases: detected ? [
                'Valid payment information',
                'Invalid credit card number',
                'Expired credit card',
                'CVV validation',
                'Billing address validation',
                'Shipping address validation',
                'Order total calculation',
                'Payment processing errors'
            ] : []
        };
    }

    detectNavigationPattern(pageAnalysis) {
        const { structure, elements } = pageAnalysis;

        const hasMainNavigation = structure.hasNavigation;
        const hasMenuLinks = elements.links.filter(link =>
            link.className?.toLowerCase().includes('nav') ||
            link.className?.toLowerCase().includes('menu')
        ).length > 2;

        const hasBreadcrumbs = elements.links.some(link =>
            link.className?.toLowerCase().includes('breadcrumb')
        ) || pageAnalysis.semantics.landmarks.some(landmark =>
            landmark.ariaLabel?.toLowerCase().includes('breadcrumb')
        );

        const detected = hasMainNavigation || hasMenuLinks;

        return {
            detected,
            confidence: detected ? this.calculateConfidence([
                hasMainNavigation,
                hasMenuLinks,
                hasBreadcrumbs
            ]) : 0,
            elements: detected ? {
                navigationLinks: elements.links.filter(link =>
                    link.className?.toLowerCase().includes('nav') ||
                    link.className?.toLowerCase().includes('menu')
                ),
                breadcrumbs: elements.links.filter(link =>
                    link.className?.toLowerCase().includes('breadcrumb')
                ),
                mobileMenu: elements.buttons.find(button =>
                    button.className?.toLowerCase().includes('hamburger') ||
                    button.className?.toLowerCase().includes('menu-toggle')
                )
            } : null,
            testCases: detected ? [
                'Main navigation links functionality',
                'Mobile menu toggle',
                'Breadcrumb navigation',
                'Active page highlighting',
                'Dropdown menu interactions',
                'Keyboard navigation'
            ] : []
        };
    }

    detectCrudPattern(pageAnalysis) {
        const { elements, tables } = pageAnalysis;

        const hasDataTable = pageAnalysis.elements.tables.length > 0;
        const hasCreateButton = elements.buttons.some(button =>
            button.text?.toLowerCase().includes('create') ||
            button.text?.toLowerCase().includes('add') ||
            button.text?.toLowerCase().includes('new')
        );

        const hasEditActions = elements.buttons.some(button =>
            button.text?.toLowerCase().includes('edit') ||
            button.text?.toLowerCase().includes('update')
        );

        const hasDeleteActions = elements.buttons.some(button =>
            button.text?.toLowerCase().includes('delete') ||
            button.text?.toLowerCase().includes('remove')
        );

        const detected = hasDataTable && (hasCreateButton || hasEditActions || hasDeleteActions);

        return {
            detected,
            confidence: detected ? this.calculateConfidence([
                hasDataTable,
                hasCreateButton,
                hasEditActions,
                hasDeleteActions
            ]) : 0,
            elements: detected ? {
                dataTable: pageAnalysis.elements.tables[0],
                createButton: elements.buttons.find(button =>
                    button.text?.toLowerCase().includes('create') ||
                    button.text?.toLowerCase().includes('add')
                ),
                editButtons: elements.buttons.filter(button =>
                    button.text?.toLowerCase().includes('edit')
                ),
                deleteButtons: elements.buttons.filter(button =>
                    button.text?.toLowerCase().includes('delete')
                )
            } : null,
            testCases: detected ? [
                'Create new record',
                'Edit existing record',
                'Delete record with confirmation',
                'Bulk operations',
                'Data validation',
                'Search and filter data',
                'Pagination navigation',
                'Sort by columns'
            ] : []
        };
    }

    detectModalPattern(pageAnalysis) {
        const { structure, elements } = pageAnalysis;

        const hasModals = structure.hasModals;
        const hasModalTriggers = elements.buttons.some(button =>
            button.className?.toLowerCase().includes('modal') ||
            button.ariaLabel?.toLowerCase().includes('open') ||
            button.dataTestId?.toLowerCase().includes('modal')
        );

        const detected = hasModals || hasModalTriggers;

        return {
            detected,
            confidence: detected ? this.calculateConfidence([hasModals, hasModalTriggers]) : 0,
            elements: detected ? {
                modalTriggers: elements.buttons.filter(button =>
                    button.className?.toLowerCase().includes('modal') ||
                    button.dataTestId?.toLowerCase().includes('modal')
                )
            } : null,
            testCases: detected ? [
                'Open modal dialog',
                'Close modal with X button',
                'Close modal with ESC key',
                'Close modal by clicking backdrop',
                'Modal content validation',
                'Modal form submission',
                'Multiple modal handling'
            ] : []
        };
    }

    detectPaginationPattern(pageAnalysis) {
        const { elements } = pageAnalysis;

        const paginationKeywords = ['next', 'previous', 'prev', 'page'];
        const hasPaginationButtons = elements.buttons.some(button =>
            paginationKeywords.some(keyword =>
                button.text?.toLowerCase().includes(keyword)
            )
        );

        const hasPaginationLinks = elements.links.some(link =>
            paginationKeywords.some(keyword =>
                link.text?.toLowerCase().includes(keyword)
            ) || /^\d+$/.test(link.text?.trim())
        );

        const detected = hasPaginationButtons || hasPaginationLinks;

        return {
            detected,
            confidence: detected ? this.calculateConfidence([hasPaginationButtons, hasPaginationLinks]) : 0,
            elements: detected ? {
                nextButton: elements.buttons.find(button =>
                    button.text?.toLowerCase().includes('next')
                ),
                prevButton: elements.buttons.find(button =>
                    button.text?.toLowerCase().includes('prev')
                ),
                pageNumbers: elements.links.filter(link =>
                    /^\d+$/.test(link.text?.trim())
                )
            } : null,
            testCases: detected ? [
                'Navigate to next page',
                'Navigate to previous page',
                'Jump to specific page number',
                'First and last page navigation',
                'Page size selection',
                'URL update on pagination'
            ] : []
        };
    }

    detectFiltersPattern(pageAnalysis) {
        const { elements } = pageAnalysis;

        const hasFilterInputs = elements.inputs.some(input =>
            input.name?.toLowerCase().includes('filter') ||
            input.placeholder?.toLowerCase().includes('filter')
        );

        const hasFilterSelects = elements.selects.some(select =>
            select.name?.toLowerCase().includes('filter') ||
            select.className?.toLowerCase().includes('filter')
        );

        const hasFilterButtons = elements.buttons.some(button =>
            button.text?.toLowerCase().includes('filter') ||
            button.text?.toLowerCase().includes('apply')
        );

        const detected = hasFilterInputs || hasFilterSelects || hasFilterButtons;

        return {
            detected,
            confidence: detected ? this.calculateConfidence([
                hasFilterInputs,
                hasFilterSelects,
                hasFilterButtons
            ]) : 0,
            elements: detected ? {
                filterInputs: elements.inputs.filter(input =>
                    input.name?.toLowerCase().includes('filter')
                ),
                filterSelects: elements.selects.filter(select =>
                    select.name?.toLowerCase().includes('filter')
                ),
                applyButton: elements.buttons.find(button =>
                    button.text?.toLowerCase().includes('apply') ||
                    button.text?.toLowerCase().includes('filter')
                ),
                clearButton: elements.buttons.find(button =>
                    button.text?.toLowerCase().includes('clear') ||
                    button.text?.toLowerCase().includes('reset')
                )
            } : null,
            testCases: detected ? [
                'Apply single filter',
                'Apply multiple filters',
                'Clear all filters',
                'Filter validation',
                'Filter persistence',
                'Filter with search'
            ] : []
        };
    }

    detectFileUploadPattern(pageAnalysis) {
        const { elements } = pageAnalysis;

        const hasFileInputs = elements.inputs.some(input => input.type === 'file');
        const hasUploadButtons = elements.buttons.some(button =>
            button.text?.toLowerCase().includes('upload') ||
            button.text?.toLowerCase().includes('browse')
        );

        const detected = hasFileInputs || hasUploadButtons;

        return {
            detected,
            confidence: detected ? this.calculateConfidence([hasFileInputs, hasUploadButtons]) : 0,
            elements: detected ? {
                fileInputs: elements.inputs.filter(input => input.type === 'file'),
                uploadButtons: elements.buttons.filter(button =>
                    button.text?.toLowerCase().includes('upload')
                )
            } : null,
            testCases: detected ? [
                'Upload valid file',
                'Upload invalid file type',
                'Upload oversized file',
                'Multiple file upload',
                'Drag and drop upload',
                'Upload progress indication'
            ] : []
        };
    }

    detectFormValidationPattern(pageAnalysis) {
        const { elements } = pageAnalysis;

        const hasRequiredFields = elements.inputs.some(input => input.required);
        const hasPatternValidation = elements.inputs.some(input => input.pattern);
        const hasLengthValidation = elements.inputs.some(input =>
            input.minLength || input.maxLength
        );

        const detected = hasRequiredFields || hasPatternValidation || hasLengthValidation;

        return {
            detected,
            confidence: detected ? this.calculateConfidence([
                hasRequiredFields,
                hasPatternValidation,
                hasLengthValidation
            ]) : 0,
            elements: detected ? {
                requiredFields: elements.inputs.filter(input => input.required),
                patternFields: elements.inputs.filter(input => input.pattern),
                lengthValidatedFields: elements.inputs.filter(input =>
                    input.minLength || input.maxLength
                )
            } : null,
            testCases: detected ? [
                'Required field validation',
                'Email format validation',
                'Phone number validation',
                'Password strength validation',
                'Field length validation',
                'Custom pattern validation',
                'Real-time validation feedback'
            ] : []
        };
    }

    detectDataTablePattern(pageAnalysis) {
        const { tables } = pageAnalysis;

        const hasDataTable = pageAnalysis.elements.tables.length > 0;
        const hasSortableColumns = pageAnalysis.elements.buttons.some(button =>
            button.className?.toLowerCase().includes('sort')
        );

        const detected = hasDataTable;

        return {
            detected,
            confidence: detected ? this.calculateConfidence([hasDataTable, hasSortableColumns]) : 0,
            elements: detected ? {
                table: pageAnalysis.elements.tables[0],
                sortButtons: pageAnalysis.elements.buttons.filter(button =>
                    button.className?.toLowerCase().includes('sort')
                )
            } : null,
            testCases: detected ? [
                'Table data display',
                'Column sorting',
                'Row selection',
                'Table pagination',
                'Column filtering',
                'Export table data'
            ] : []
        };
    }

    detectSearchFilters(elements) {
        return elements.selects.filter(select =>
            select.name?.toLowerCase().includes('filter') ||
            select.name?.toLowerCase().includes('category') ||
            select.name?.toLowerCase().includes('type')
        );
    }

    detectSortingOptions(elements) {
        return elements.selects.filter(select =>
            select.name?.toLowerCase().includes('sort') ||
            select.name?.toLowerCase().includes('order')
        );
    }

    detectWorkflows(patterns, pageAnalysis) {
        const workflows = {};

        // E-commerce workflow
        if (patterns.search && patterns.checkout) {
            workflows.ecommerce = {
                name: 'E-commerce Shopping',
                steps: ['Search products', 'Add to cart', 'Checkout', 'Payment'],
                patterns: ['search', 'checkout']
            };
        }

        // User management workflow
        if (patterns.login && patterns.registration) {
            workflows.userManagement = {
                name: 'User Management',
                steps: ['Registration', 'Login', 'Profile management'],
                patterns: ['registration', 'login']
            };
        }

        // Data management workflow
        if (patterns.crud && patterns.filters) {
            workflows.dataManagement = {
                name: 'Data Management',
                steps: ['View data', 'Filter/search', 'Create', 'Edit', 'Delete'],
                patterns: ['crud', 'filters', 'search']
            };
        }

        // Content management workflow
        if (patterns.crud && patterns.fileUpload) {
            workflows.contentManagement = {
                name: 'Content Management',
                steps: ['Upload files', 'Create content', 'Edit content', 'Publish'],
                patterns: ['crud', 'fileUpload']
            };
        }

        return workflows;
    }

    calculateConfidence(conditions) {
        const trueConditions = conditions.filter(condition => condition).length;
        return Math.round((trueConditions / conditions.length) * 100);
    }

    generatePatternSummary(patterns, workflows) {
        const detectedPatternNames = Object.keys(patterns);
        const workflowNames = Object.keys(workflows);

        return {
            totalPatterns: detectedPatternNames.length,
            patterns: detectedPatternNames,
            workflows: workflowNames,
            complexity: this.assessComplexity(detectedPatternNames, workflowNames),
            recommendations: this.generateRecommendations(patterns, workflows)
        };
    }

    assessComplexity(patterns, workflows) {
        const totalItems = patterns.length + workflows.length;

        if (totalItems <= 2) return 'Simple';
        if (totalItems <= 5) return 'Medium';
        return 'Complex';
    }

    generateRecommendations(patterns, workflows) {
        const recommendations = [];

        if (patterns.login) {
            recommendations.push('Implement comprehensive authentication tests including security scenarios');
        }

        if (patterns.formValidation) {
            recommendations.push('Add extensive form validation testing with edge cases');
        }

        if (patterns.crud) {
            recommendations.push('Include data integrity and concurrent access tests');
        }

        if (patterns.fileUpload) {
            recommendations.push('Test various file types, sizes, and error conditions');
        }

        if (Object.keys(workflows).length > 1) {
            recommendations.push('Consider end-to-end workflow tests that span multiple patterns');
        }

        return recommendations;
    }
}