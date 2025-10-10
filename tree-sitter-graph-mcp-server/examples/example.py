#!/usr/bin/env python3
"""
Python example for Tree-sitter MCP testing
Demonstrates classes, functions, decorators, and async code
"""

import asyncio
from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass
class Person:
    """A person with name and age."""
    name: str
    age: int
    email: Optional[str] = None
    
    def greet(self) -> str:
        """Return a greeting message."""
        return f"Hello, I'm {self.name} and I'm {self.age} years old."


class Calculator:
    """Simple calculator class with basic operations."""
    
    def __init__(self, initial_value: float = 0):
        self.value = initial_value
        self.history: List[str] = []
    
    def add(self, x: float) -> float:
        """Add a number to the current value."""
        self.value += x
        self.history.append(f"Added {x}")
        return self.value
    
    def multiply(self, x: float) -> float:
        """Multiply the current value by a number."""
        self.value *= x
        self.history.append(f"Multiplied by {x}")
        return self.value
    
    @property
    def result(self) -> float:
        """Get the current result."""
        return self.value


async def fetch_data(url: str) -> Dict:
    """Simulate async data fetching."""
    await asyncio.sleep(1)
    return {"url": url, "status": "success", "data": [1, 2, 3]}


def fibonacci(n: int) -> int:
    """Calculate fibonacci number recursively."""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


# Lambda function
square = lambda x: x ** 2

# List comprehension
even_squares = [x**2 for x in range(10) if x % 2 == 0]

# Dictionary comprehension
word_lengths = {word: len(word) for word in ["hello", "world", "python"]}


if __name__ == "__main__":
    # Create instances and test
    person = Person("Alice", 30, "alice@example.com")
    print(person.greet())
    
    calc = Calculator(10)
    calc.add(5)
    calc.multiply(2)
    print(f"Result: {calc.result}")
    
    # Test fibonacci
    print(f"Fibonacci(10): {fibonacci(10)}")
    
    # Run async function
    asyncio.run(fetch_data("https://api.example.com"))