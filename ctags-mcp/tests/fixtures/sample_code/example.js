/**
 * Example JavaScript file for testing CTags functionality
 */

class Calculator {
    constructor() {
        this.result = 0;
    }
    
    add(a, b) {
        this.result = a + b;
        return this.result;
    }
    
    subtract(a, b) {
        this.result = a - b;
        return this.result;
    }
    
    multiply(a, b) {
        this.result = a * b;
        return this.result;
    }
    
    divide(a, b) {
        if (b === 0) {
            throw new Error("Division by zero");
        }
        this.result = a / b;
        return this.result;
    }
    
    static square(n) {
        return n * n;
    }
}

function processArray(arr) {
    return arr.map(item => item * 2);
}

const filterEven = (numbers) => {
    return numbers.filter(n => n % 2 === 0);
};

async function fetchData(url) {
    try {
        const response = await fetch(url);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Fetch error:", error);
        return null;
    }
}

// Constants
const API_URL = "https://api.example.com";
const MAX_RETRIES = 3;
const TIMEOUT = 5000;

// Object with methods
const utils = {
    formatDate(date) {
        return date.toISOString();
    },
    
    parseJSON(str) {
        try {
            return JSON.parse(str);
        } catch {
            return null;
        }
    }
};

export { Calculator, processArray, filterEven, fetchData, utils };