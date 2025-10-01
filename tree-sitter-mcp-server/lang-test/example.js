/**
 * JavaScript example for Tree-sitter MCP testing
 * Demonstrates ES6+ features, classes, async/await, and various patterns
 */

// ES6 Class with inheritance
class Animal {
    constructor(name, species) {
        this.name = name;
        this.species = species;
    }
    
    speak() {
        return `${this.name} makes a sound.`;
    }
    
    static compareAge(animal1, animal2) {
        return animal1.age - animal2.age;
    }
}

class Dog extends Animal {
    constructor(name, breed) {
        super(name, 'Canine');
        this.breed = breed;
        this.tricks = [];
    }
    
    speak() {
        return `${this.name} barks!`;
    }
    
    learnTrick(trick) {
        this.tricks.push(trick);
        return this;
    }
}

// Arrow functions and destructuring
const processData = ({ name, age, ...rest }) => {
    const isAdult = age >= 18;
    return {
        displayName: name.toUpperCase(),
        isAdult,
        metadata: { ...rest, processed: true }
    };
};

// Async/await with error handling
async function fetchUserData(userId) {
    try {
        const response = await fetch(`/api/users/${userId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Failed to fetch user:', error);
        return null;
    }
}

// Generator function
function* fibonacci() {
    let [prev, curr] = [0, 1];
    while (true) {
        yield curr;
        [prev, curr] = [curr, prev + curr];
    }
}

// Promise chain
const processOrder = (orderId) => {
    return validateOrder(orderId)
        .then(order => calculateTotal(order))
        .then(total => applyDiscount(total))
        .then(finalAmount => chargePayment(finalAmount))
        .catch(error => {
            console.error('Order processing failed:', error);
            throw error;
        });
};

// Template literals and tagged templates
const sql = (strings, ...values) => {
    return strings.reduce((result, str, i) => {
        return result + str + (values[i] ? `'${values[i]}'` : '');
    }, '');
};

const query = sql`SELECT * FROM users WHERE name = ${userName} AND age > ${minAge}`;

// Object methods and computed properties
const calculator = {
    value: 0,
    
    add(x) {
        this.value += x;
        return this;
    },
    
    multiply(x) {
        this.value *= x;
        return this;
    },
    
    ['get' + 'Result']() {
        return this.value;
    }
};

// Array methods and functional programming
const numbers = [1, 2, 3, 4, 5];
const doubled = numbers.map(n => n * 2);
const evens = numbers.filter(n => n % 2 === 0);
const sum = numbers.reduce((acc, n) => acc + n, 0);

// Module exports (ES6)
export { Animal, Dog, fetchUserData, fibonacci };
export default calculator;