#!/usr/bin/env python3
"""
Sample Python code for testing tree-sitter-graph generation.
This file contains various Python constructs to demonstrate graph generation.
"""

import sys
import os
from typing import List, Optional, Dict
from dataclasses import dataclass

# Constants
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

@dataclass
class Config:
    """Configuration dataclass."""
    host: str
    port: int
    debug: bool = False

class Animal:
    """Base class for all animals."""
    
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
    
    def speak(self) -> str:
        """Make the animal speak."""
        raise NotImplementedError("Subclasses must implement speak()")
    
    def info(self) -> Dict[str, any]:
        """Get animal information."""
        return {
            "name": self.name,
            "age": self.age,
            "type": self.__class__.__name__
        }

class Dog(Animal):
    """Dog class inheriting from Animal."""
    
    def __init__(self, name: str, age: int, breed: str):
        super().__init__(name, age)
        self.breed = breed
    
    def speak(self) -> str:
        """Dogs bark."""
        return f"{self.name} says Woof!"
    
    def fetch(self, item: str) -> str:
        """Dogs can fetch items."""
        return f"{self.name} fetched the {item}"

class Cat(Animal):
    """Cat class inheriting from Animal."""
    
    def __init__(self, name: str, age: int, indoor: bool = True):
        super().__init__(name, age)
        self.indoor = indoor
    
    def speak(self) -> str:
        """Cats meow."""
        return f"{self.name} says Meow!"
    
    def purr(self) -> str:
        """Cats can purr."""
        return f"{self.name} is purring"

def create_animal(animal_type: str, name: str, age: int) -> Optional[Animal]:
    """
    Factory function to create animals.
    
    Args:
        animal_type: Type of animal to create
        name: Name of the animal
        age: Age of the animal
    
    Returns:
        An Animal instance or None
    """
    animal_map = {
        "dog": Dog,
        "cat": Cat
    }
    
    animal_class = animal_map.get(animal_type.lower())
    if animal_class:
        if animal_type == "dog":
            return animal_class(name, age, "Mixed")
        else:
            return animal_class(name, age)
    return None

@dataclass
class Zoo:
    """A zoo containing multiple animals."""
    name: str
    animals: List[Animal]
    
    def add_animal(self, animal: Animal) -> None:
        """Add an animal to the zoo."""
        self.animals.append(animal)
    
    def all_speak(self) -> List[str]:
        """Make all animals speak."""
        return [animal.speak() for animal in self.animals]
    
    def find_by_name(self, name: str) -> Optional[Animal]:
        """Find an animal by name."""
        for animal in self.animals:
            if animal.name == name:
                return animal
        return None

async def async_operation() -> str:
    """An async function example."""
    return "async result"

def decorator_example(func):
    """A decorator function."""
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@decorator_example
def decorated_function(x: int, y: int) -> int:
    """A decorated function that adds two numbers."""
    return x + y

def main():
    """Main entry point."""
    # Create some animals
    dog = create_animal("dog", "Buddy", 3)
    cat = create_animal("cat", "Whiskers", 5)
    
    # Create a zoo
    zoo = Zoo("Happy Zoo", [])
    
    # Add animals to zoo
    if dog:
        zoo.add_animal(dog)
        print(dog.speak())
    
    if cat:
        zoo.add_animal(cat)
        print(cat.speak())
    
    # Make all animals speak
    sounds = zoo.all_speak()
    for sound in sounds:
        print(sound)
    
    # Test decorated function
    result = decorated_function(5, 3)
    print(f"Result: {result}")

if __name__ == "__main__":
    main()