"""
Utility functions for the test project
"""

class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        """Add two numbers."""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def subtract(self, a, b):
        """Subtract two numbers."""
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result
    
    def multiply(self, a, b):
        """Multiply two numbers."""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def get_history(self):
        """Get calculation history."""
        return self.history

def log_message(message):
    """Log a message with timestamp."""
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def validate_input(value):
    """Validate input value."""
    if isinstance(value, (int, float)):
        return True
    return False

# Multiple function calls for testing
def test_functions():
    """Test various function calls."""
    log_message("Starting tests")
    log_message("Testing calculator")
    
    calc = Calculator()
    calc.add(1, 2)
    calc.subtract(5, 3)
    calc.multiply(4, 6)
    
    log_message("Tests completed")
    log_message("All done!")