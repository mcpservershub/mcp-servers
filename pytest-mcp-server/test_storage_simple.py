#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pytest_mcp_server.storage import TestStorage
import sqlite3

# Test basic database functionality
print("Testing database initialization...")

storage = TestStorage()
print(f"Database path: {storage.db_path}")

# Try to manually check if tables exist
try:
    conn = sqlite3.connect(storage.db_path, check_same_thread=False)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables found: {[t[0] for t in tables]}")
    conn.close()
except Exception as e:
    print(f"Error checking tables: {e}")

# Try creating a session
print("\nTesting session creation...")
from pytest_mcp_server.models import TestEnvironment, TestSession
from uuid import uuid4

try:
    env = TestEnvironment(os="Linux", python_version="3.12.0")
    session = TestSession(session_id=str(uuid4()), environment=env)
    storage.store_session(session)
    print(f"Session stored successfully: {session.session_id}")
except Exception as e:
    print(f"Error storing session: {e}")