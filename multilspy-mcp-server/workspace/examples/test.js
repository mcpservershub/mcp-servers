/**
 * Sample JavaScript file for testing LSP features
 */

class Calculator {
    constructor() {
        this.result = 0;
        this.history = [];
    }

    /**
     * Add two numbers
     * @param {number} a - First number
     * @param {number} b - Second number
     * @returns {number} Sum of a and b
     */
    add(a, b) {
        const result = a + b;
        this.history.push(`${a} + ${b} = ${result}`);
        this.result = result;
        return result;
    }

    /**
     * Multiply two numbers
     * @param {number} a - First number
     * @param {number} b - Second number
     * @returns {number} Product of a and b
     */
    multiply(a, b) {
        const result = a * b;
        this.history.push(`${a} * ${b} = ${result}`);
        this.result = result;
        return result;
    }

    /**
     * Divide two numbers
     * @param {number} a - Dividend
     * @param {number} b - Divisor
     * @returns {number} Quotient
     * @throws {Error} When dividing by zero
     */
    divide(a, b) {
        if (b === 0) {
            throw new Error("Cannot divide by zero");
        }
        const result = a / b;
        this.history.push(`${a} / ${b} = ${result}`);
        this.result = result;
        return result;
    }

    /**
     * Get calculation history
     * @returns {Array<string>} Array of calculation history
     */
    getHistory() {
        return this.history;
    }

    /**
     * Clear history and reset result
     */
    reset() {
        this.result = 0;
        this.history = [];
    }
}

// Utility functions
function formatNumber(num) {
    return new Intl.NumberFormat('en-US').format(num);
}

function isValidNumber(value) {
    return typeof value === 'number' && !isNaN(value) && isFinite(value);
}

// Main function to demonstrate usage
function main() {
    const calc = new Calculator();
    
    console.log("Calculator Demo");
    console.log("===============");
    
    // Perform calculations
    const sum = calc.add(10, 5);
    console.log(`10 + 5 = ${sum}`);
    
    const product = calc.multiply(4, 7);
    console.log(`4 * 7 = ${product}`);
    
    try {
        const quotient = calc.divide(20, 4);
        console.log(`20 / 4 = ${quotient}`);
        
        // This will throw an error
        // calc.divide(10, 0);
    } catch (error) {
        console.error(`Error: ${error.message}`);
    }
    
    // Display history
    console.log("\nCalculation History:");
    calc.getHistory().forEach(entry => {
        console.log(`  - ${entry}`);
    });
    
    // Format large number
    const largeNum = 1234567.89;
    console.log(`\nFormatted number: ${formatNumber(largeNum)}`);
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Calculator, formatNumber, isValidNumber };
}

// Run main if this is the entry point
if (require.main === module) {
    main();
}