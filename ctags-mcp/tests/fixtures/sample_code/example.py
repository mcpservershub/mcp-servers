#!/usr/bin/env python3
"""Example Python file for testing CTags functionality."""

import os
import sys
from typing import List, Dict, Optional


class DatabaseConnection:
    """Database connection handler."""
    
    def __init__(self, host: str, port: int = 5432):
        """Initialize database connection.
        
        Args:
            host: Database host
            port: Database port
        """
        self.host = host
        self.port = port
        self._connection = None
    
    def connect(self) -> bool:
        """Establish database connection."""
        try:
            # Simulate connection
            self._connection = f"Connected to {self.host}:{self.port}"
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def disconnect(self) -> None:
        """Close database connection."""
        self._connection = None
    
    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connection is not None


class UserModel:
    """User data model."""
    
    def __init__(self, user_id: int, username: str):
        self.user_id = user_id
        self.username = username
        self.email: Optional[str] = None
    
    def set_email(self, email: str) -> None:
        """Set user email."""
        self.email = email
    
    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email
        }


def get_all_users(db: DatabaseConnection) -> List[UserModel]:
    """Retrieve all users from database.
    
    Args:
        db: Database connection
        
    Returns:
        List of users
    """
    if not db.is_connected:
        return []
    
    # Simulate fetching users
    users = [
        UserModel(1, "alice"),
        UserModel(2, "bob"),
        UserModel(3, "charlie")
    ]
    return users


def find_user_by_id(user_id: int, users: List[UserModel]) -> Optional[UserModel]:
    """Find user by ID.
    
    Args:
        user_id: User ID to search
        users: List of users
        
    Returns:
        User if found, None otherwise
    """
    for user in users:
        if user.user_id == user_id:
            return user
    return None


def main():
    """Main entry point."""
    db = DatabaseConnection("localhost")
    
    if db.connect():
        users = get_all_users(db)
        print(f"Found {len(users)} users")
        
        user = find_user_by_id(1, users)
        if user:
            print(f"User found: {user.username}")
        
        db.disconnect()


# Global constants
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 5432
MAX_CONNECTIONS = 100

if __name__ == "__main__":
    main()