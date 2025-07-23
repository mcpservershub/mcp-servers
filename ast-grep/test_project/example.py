#!/usr/bin/env python3
"""
Example Python file for testing ast-grep MCP server
"""

def calculate_sum(a, b):
    """Calculate the sum of two numbers."""
    result = a + b
    print(f"The sum is: {result}")
    return result

def calculate_product(x, y):
    """Calculate the product of two numbers."""
    result = x * y
    print(f"The product is: {result}")
    return result

def process_data():
    """Process some data using our calculation functions."""
    # Test multiple occurrences of calculate_sum
    sum1 = calculate_sum(5, 3)
    sum2 = calculate_sum(10, 20)
    sum3 = calculate_sum(1, 2)
    
    # Test calculate_product
    product1 = calculate_product(4, 6)
    product2 = calculate_product(2, 8)
    
    # Use calculate_sum again
    final_sum = calculate_sum(sum1, sum2)
    
    return final_sum, product1, product2

if __name__ == "__main__":
    # Call calculate_sum one more time
    initial = calculate_sum(0, 1)
    result = process_data()
    print(f"Final results: {result}")