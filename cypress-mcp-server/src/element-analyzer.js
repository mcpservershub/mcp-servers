import puppeteer from 'puppeteer';
import * as cheerio from 'cheerio';

export class ElementAnalyzer {
    constructor() {
        this.browser = null;
    }

    async initBrowser() {
        if (!this.browser) {
            this.browser = await puppeteer.launch({
                headless: 'new',
                args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            });
        }
        return this.browser;
    }

    async analyzePage(url) {
        const browser = await this.initBrowser();
        const page = await browser.newPage();

        try {
            // Set viewport for consistent analysis
            await page.setViewport({ width: 1920, height: 1080 });

            // Navigate to page
            await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });

            // Get page content and metadata
            const [html, title, currentUrl] = await Promise.all([
                page.content(),
                page.title(),
                page.url()
            ]);

            // Parse HTML with Cheerio
            const $ = cheerio.load(html);

            // Analyze different element types
            const elements = {
                buttons: this.analyzeButtons($),
                inputs: this.analyzeInputs($),
                links: this.analyzeLinks($),
                forms: this.analyzeForms($),
                selects: this.analyzeSelects($),
                textareas: this.analyzeTextareas($),
                images: this.analyzeImages($),
                tables: this.analyzeTables($),
                lists: this.analyzeLists($)
            };

            // Get page structure information
            const structure = {
                hasNavigation: $('nav, .nav, .navbar, .navigation').length > 0,
                hasHeader: $('header, .header').length > 0,
                hasFooter: $('footer, .footer').length > 0,
                hasSidebar: $('aside, .sidebar, .side-nav').length > 0,
                hasModals: $('.modal, .dialog, .popup').length > 0,
                hasCarousel: $('.carousel, .slider, .swiper').length > 0
            };

            // Extract semantic information
            const semantics = {
                headings: this.extractHeadings($),
                landmarks: this.extractLandmarks($),
                metadata: this.extractMetadata($),
                schema: this.extractSchemaOrg($)
            };

            // Analyze accessibility features
            const accessibility = {
                hasAriaLabels: $('[aria-label]').length > 0,
                hasAriaDescriptions: $('[aria-describedby]').length > 0,
                hasSkipLinks: $('a[href^="#"]').filter((i, el) => $(el).text().toLowerCase().includes('skip')).length > 0,
                hasAltTexts: $('img[alt]').length > 0,
                formLabels: $('label').length
            };

            return {
                url: currentUrl,
                title,
                elements,
                structure,
                semantics,
                accessibility,
                pageInfo: {
                    htmlLength: html.length,
                    elementCount: $('*').length,
                    textLength: $.text().length
                }
            };

        } catch (error) {
            throw new Error(`Page analysis failed for ${url}: ${error.message}`);
        } finally {
            await page.close();
        }
    }

    analyzeButtons($) {
        const buttons = [];

        $('button, input[type="button"], input[type="submit"], input[type="reset"], .btn').each((index, element) => {
            const $el = $(element);
            buttons.push({
                index,
                tagName: element.tagName,
                id: $el.attr('id'),
                className: $el.attr('class'),
                text: $el.text().trim(),
                value: $el.attr('value'),
                type: $el.attr('type'),
                disabled: $el.is(':disabled'),
                ariaLabel: $el.attr('aria-label'),
                dataTestId: $el.attr('data-testid'),
                role: $el.attr('role'),
                onclick: $el.attr('onclick'),
                formAction: $el.attr('formaction'),
                suggested: {
                    locator: this.generateOptimalLocator($el),
                    method: this.suggestElementMethod($el, 'button')
                }
            });
        });

        return buttons;
    }

    analyzeInputs($) {
        const inputs = [];

        $('input').each((index, element) => {
            const $el = $(element);
            const inputType = $el.attr('type') || 'text';

            inputs.push({
                index,
                id: $el.attr('id'),
                name: $el.attr('name'),
                type: inputType,
                className: $el.attr('class'),
                placeholder: $el.attr('placeholder'),
                value: $el.attr('value'),
                required: $el.is('[required]'),
                disabled: $el.is(':disabled'),
                readonly: $el.is('[readonly]'),
                pattern: $el.attr('pattern'),
                minLength: $el.attr('minlength'),
                maxLength: $el.attr('maxlength'),
                min: $el.attr('min'),
                max: $el.attr('max'),
                step: $el.attr('step'),
                autocomplete: $el.attr('autocomplete'),
                ariaLabel: $el.attr('aria-label'),
                dataTestId: $el.attr('data-testid'),
                associatedLabel: this.findAssociatedLabel($el, $),
                suggested: {
                    locator: this.generateOptimalLocator($el),
                    method: this.suggestElementMethod($el, 'input', inputType)
                }
            });
        });

        return inputs;
    }

    analyzeLinks($) {
        const links = [];

        $('a[href]').each((index, element) => {
            const $el = $(element);
            links.push({
                index,
                id: $el.attr('id'),
                className: $el.attr('class'),
                text: $el.text().trim(),
                href: $el.attr('href'),
                title: $el.attr('title'),
                target: $el.attr('target'),
                download: $el.attr('download'),
                rel: $el.attr('rel'),
                ariaLabel: $el.attr('aria-label'),
                dataTestId: $el.attr('data-testid'),
                isExternal: this.isExternalLink($el.attr('href')),
                suggested: {
                    locator: this.generateOptimalLocator($el),
                    method: this.suggestElementMethod($el, 'link')
                }
            });
        });

        return links;
    }

    analyzeForms($) {
        const forms = [];

        $('form').each((index, element) => {
            const $form = $(element);
            const formElements = [];

            // Find all form elements within this form
            $form.find('input, select, textarea, button').each((i, el) => {
                const $el = $(el);
                formElements.push({
                    tagName: el.tagName,
                    type: $el.attr('type'),
                    name: $el.attr('name'),
                    id: $el.attr('id'),
                    required: $el.is('[required]'),
                    locator: this.generateOptimalLocator($el)
                });
            });

            forms.push({
                index,
                id: $form.attr('id'),
                className: $form.attr('class'),
                action: $form.attr('action'),
                method: $form.attr('method') || 'GET',
                enctype: $form.attr('enctype'),
                novalidate: $form.is('[novalidate]'),
                elements: formElements,
                suggested: {
                    locator: this.generateOptimalLocator($form),
                    workflow: this.suggestFormWorkflow($form, formElements)
                }
            });
        });

        return forms;
    }

    analyzeSelects($) {
        const selects = [];

        $('select').each((index, element) => {
            const $el = $(element);
            const options = [];

            $el.find('option').each((i, opt) => {
                const $opt = $(opt);
                options.push({
                    value: $opt.attr('value'),
                    text: $opt.text().trim(),
                    selected: $opt.is(':selected'),
                    disabled: $opt.is(':disabled')
                });
            });

            selects.push({
                index,
                id: $el.attr('id'),
                name: $el.attr('name'),
                className: $el.attr('class'),
                multiple: $el.is('[multiple]'),
                required: $el.is('[required]'),
                disabled: $el.is(':disabled'),
                size: $el.attr('size'),
                ariaLabel: $el.attr('aria-label'),
                dataTestId: $el.attr('data-testid'),
                options,
                suggested: {
                    locator: this.generateOptimalLocator($el),
                    method: this.suggestElementMethod($el, 'select')
                }
            });
        });

        return selects;
    }

    analyzeTextareas($) {
        const textareas = [];

        $('textarea').each((index, element) => {
            const $el = $(element);
            textareas.push({
                index,
                id: $el.attr('id'),
                name: $el.attr('name'),
                className: $el.attr('class'),
                placeholder: $el.attr('placeholder'),
                rows: $el.attr('rows'),
                cols: $el.attr('cols'),
                maxLength: $el.attr('maxlength'),
                required: $el.is('[required]'),
                disabled: $el.is(':disabled'),
                readonly: $el.is('[readonly]'),
                wrap: $el.attr('wrap'),
                ariaLabel: $el.attr('aria-label'),
                dataTestId: $el.attr('data-testid'),
                suggested: {
                    locator: this.generateOptimalLocator($el),
                    method: this.suggestElementMethod($el, 'textarea')
                }
            });
        });

        return textareas;
    }

    analyzeImages($) {
        const images = [];

        $('img').each((index, element) => {
            const $el = $(element);
            images.push({
                index,
                src: $el.attr('src'),
                alt: $el.attr('alt'),
                title: $el.attr('title'),
                id: $el.attr('id'),
                className: $el.attr('class'),
                width: $el.attr('width'),
                height: $el.attr('height'),
                loading: $el.attr('loading'),
                decoding: $el.attr('decoding')
            });
        });

        return images;
    }

    analyzeTables($) {
        const tables = [];

        $('table').each((index, element) => {
            const $table = $(element);
            const headers = [];
            const rows = [];

            $table.find('th').each((i, th) => {
                headers.push($(th).text().trim());
            });

            $table.find('tbody tr, tr').each((i, tr) => {
                const cells = [];
                $(tr).find('td, th').each((j, cell) => {
                    cells.push($(cell).text().trim());
                });
                if (cells.length > 0) rows.push(cells);
            });

            tables.push({
                index,
                id: $table.attr('id'),
                className: $table.attr('class'),
                headers,
                rows,
                rowCount: rows.length,
                columnCount: headers.length || (rows[0]?.length || 0)
            });
        });

        return tables;
    }

    analyzeLists($) {
        const lists = [];

        $('ul, ol').each((index, element) => {
            const $list = $(element);
            const items = [];

            $list.find('li').each((i, li) => {
                items.push($(li).text().trim());
            });

            lists.push({
                index,
                type: element.tagName,
                id: $list.attr('id'),
                className: $list.attr('class'),
                items,
                itemCount: items.length
            });
        });

        return lists;
    }

    extractHeadings($) {
        const headings = [];
        $('h1, h2, h3, h4, h5, h6').each((index, element) => {
            const $el = $(element);
            headings.push({
                level: parseInt(element.tagName[1]),
                text: $el.text().trim(),
                id: $el.attr('id'),
                className: $el.attr('class')
            });
        });
        return headings;
    }

    extractLandmarks($) {
        const landmarks = [];
        $('main, nav, aside, header, footer, section, article').each((index, element) => {
            const $el = $(element);
            landmarks.push({
                role: element.tagName,
                id: $el.attr('id'),
                className: $el.attr('class'),
                ariaLabel: $el.attr('aria-label')
            });
        });
        return landmarks;
    }

    extractMetadata($) {
        return {
            title: $('title').text(),
            description: $('meta[name="description"]').attr('content'),
            keywords: $('meta[name="keywords"]').attr('content'),
            viewport: $('meta[name="viewport"]').attr('content'),
            charset: $('meta[charset]').attr('charset') || $('meta[http-equiv="Content-Type"]').attr('content')
        };
    }

    extractSchemaOrg($) {
        const schemas = [];
        $('script[type="application/ld+json"]').each((index, element) => {
            try {
                const schema = JSON.parse($(element).html());
                schemas.push(schema);
            } catch (e) {
                // Invalid JSON, skip
            }
        });
        return schemas;
    }

    generateOptimalLocator($el) {
        // Priority order: data-testid > id > unique class > text content > css selector

        const dataTestId = $el.attr('data-testid');
        if (dataTestId) {
            return {
                type: 'attribute',
                value: `[data-testid="${dataTestId}"]`,
                priority: 1
            };
        }

        const id = $el.attr('id');
        if (id) {
            return {
                type: 'id',
                value: `#${id}`,
                priority: 2
            };
        }

        const className = $el.attr('class');
        if (className) {
            const classes = className.split(' ').filter(c => c.trim());
            if (classes.length === 1) {
                return {
                    type: 'class',
                    value: `.${classes[0]}`,
                    priority: 3
                };
            }
        }

        const text = $el.text().trim();
        if (text && text.length < 50) {
            return {
                type: 'text',
                value: text,
                priority: 4
            };
        }

        // Fallback to tag name with index
        const tagName = $el.prop('tagName').toLowerCase();
        return {
            type: 'css',
            value: tagName,
            priority: 5
        };
    }

    suggestElementMethod($el, elementType, inputType = null) {
        switch (elementType) {
            case 'button':
                return 'click';
            case 'link':
                return 'click';
            case 'input':
                switch (inputType) {
                    case 'checkbox':
                    case 'radio':
                        return 'check';
                    case 'file':
                        return 'uploadFile';
                    case 'submit':
                    case 'button':
                        return 'click';
                    default:
                        return 'type';
                }
            case 'select':
                return 'select';
            case 'textarea':
                return 'type';
            default:
                return 'interact';
        }
    }

    suggestFormWorkflow($form, elements) {
        const hasPassword = elements.some(el => el.type === 'password');
        const hasEmail = elements.some(el => el.type === 'email' || (el.name && el.name.includes('email')));
        const hasUsername = elements.some(el => el.name && (el.name.includes('user') || el.name.includes('login')));

        if (hasPassword && (hasEmail || hasUsername)) {
            return 'login';
        }

        if (elements.some(el => el.type === 'search' || (el.name && el.name.includes('search')))) {
            return 'search';
        }

        if (elements.length > 3) {
            return 'registration';
        }

        return 'form-submission';
    }

    findAssociatedLabel($input, $) {
        const id = $input.attr('id');
        if (id) {
            const label = $(`label[for="${id}"]`);
            if (label.length > 0) {
                return label.text().trim();
            }
        }

        // Check for wrapping label
        const parentLabel = $input.closest('label');
        if (parentLabel.length > 0) {
            return parentLabel.text().trim();
        }

        return null;
    }

    isExternalLink(href) {
        if (!href) return false;
        return href.startsWith('http') && !href.includes(window?.location?.hostname || '');
    }

    async analyzeElement(url, selector, includeContext = true) {
        const browser = await this.initBrowser();
        const page = await browser.newPage();

        try {
            await page.goto(url, { waitUntil: 'networkidle2' });

            const elementInfo = await page.evaluate((sel, context) => {
                const element = document.querySelector(sel);
                if (!element) return null;

                const rect = element.getBoundingClientRect();
                const computedStyle = window.getComputedStyle(element);

                const info = {
                    tagName: element.tagName,
                    id: element.id,
                    className: element.className,
                    textContent: element.textContent?.trim(),
                    innerHTML: element.innerHTML,
                    attributes: {},
                    boundingRect: rect,
                    computedStyle: {
                        display: computedStyle.display,
                        visibility: computedStyle.visibility,
                        opacity: computedStyle.opacity,
                        position: computedStyle.position,
                        zIndex: computedStyle.zIndex
                    },
                    isVisible: rect.width > 0 && rect.height > 0 && computedStyle.visibility !== 'hidden',
                    isClickable: element.tagName === 'BUTTON' || element.tagName === 'A' || element.onclick !== null
                };

                // Get all attributes
                for (let attr of element.attributes) {
                    info.attributes[attr.name] = attr.value;
                }

                if (context) {
                    info.parentElement = {
                        tagName: element.parentElement?.tagName,
                        id: element.parentElement?.id,
                        className: element.parentElement?.className
                    };

                    info.siblings = Array.from(element.parentElement?.children || [])
                        .map(sibling => ({
                            tagName: sibling.tagName,
                            id: sibling.id,
                            className: sibling.className
                        }));

                    info.children = Array.from(element.children).map(child => ({
                        tagName: child.tagName,
                        id: child.id,
                        className: child.className
                    }));
                }

                return info;
            }, selector, includeContext);

            return elementInfo;

        } catch (error) {
            throw new Error(`Element analysis failed: ${error.message}`);
        } finally {
            await page.close();
        }
    }

    async closeBrowser() {
        if (this.browser) {
            await this.browser.close();
            this.browser = null;
        }
    }
}