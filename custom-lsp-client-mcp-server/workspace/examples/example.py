"""
Example Python file for testing MultilsPy MCP Server.
"""

from typing import List, Optional


class Calculator:
    """A simple calculator class for demonstration."""
    
    def __init__(self, initial_value: float = 0):
        """Initialize calculator with an optional starting value."""
        self.value = initial_value
        self.history: List[float] = [initial_value]
    
    def add(self, number: float) -> float:
        """Add a number to the current value."""
        self.value += number
        self.history.append(self.value)
        return self.value
    
    def subtract(self, number: float) -> float:
        """Subtract a number from the current value."""
        self.value -= number
        self.history.append(self.value)
        return self.value
    
    def multiply(self, number: float) -> float:
        """Multiply the current value by a number."""
        self.value *= number
        self.history.append(self.value)
        return self.value
    
    def divide(self, number: float) -> Optional[float]:
        """Divide the current value by a number."""
        if number == 0:
            print("Error: Division by zero")
            return None
        self.value /= number
        self.history.append(self.value)
        return self.value
    
    def get_history(self) -> List[float]:
        """Get the calculation history."""
        return self.history.copy()
    
    def reset(self) -> None:
        """Reset the calculator to zero."""
        self.value = 0
        self.history = [0]


def fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def main():
    """Main function to demonstrate the calculator."""
    calc = Calculator(10)
    
    print(f"Initial value: {calc.value}")
    print(f"After adding 5: {calc.add(5)}")
    print(f"After multiplying by 2: {calc.multiply(2)}")
    print(f"After subtracting 10: {calc.subtract(10)}")
    print(f"After dividing by 4: {calc.divide(4)}")
    
    print(f"\nCalculation history: {calc.get_history()}")
    
    # Test Fibonacci
    print(f"\nFibonacci(10): {fibonacci(10)}")


if __name__ == "__main__":
    main()