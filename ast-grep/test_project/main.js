/**
 * Example JavaScript file for testing ast-grep MCP server
 */

function calculateSum(a, b) {
    const result = a + b;
    console.log(`Sum: ${result}`);
    return result;
}

function calculateProduct(x, y) {
    const result = x * y;
    console.log(`Product: ${result}`);
    return result;
}

function processNumbers() {
    // Multiple calls to calculateSum
    const sum1 = calculateSum(10, 20);
    const sum2 = calculateSum(5, 15);
    const sum3 = calculateSum(1, 1);
    
    // Calls to calculateProduct
    const product1 = calculateProduct(3, 4);
    const product2 = calculateProduct(2, 6);
    
    // Another calculateSum call
    const finalSum = calculateSum(sum1, sum2);
    
    return {
        sums: [sum1, sum2, sum3, finalSum],
        products: [product1, product2]
    };
}

class MathHelper {
    constructor() {
        this.operations = [];
    }
    
    add(a, b) {
        const result = calculateSum(a, b);
        this.operations.push(`add: ${a} + ${b} = ${result}`);
        return result;
    }
    
    getOperations() {
        return this.operations;
    }
}

// Main execution
const helper = new MathHelper();
helper.add(7, 8);
const results = processNumbers();
console.log("Results:", results);