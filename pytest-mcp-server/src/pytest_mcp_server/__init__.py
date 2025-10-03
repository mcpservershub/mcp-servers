"""
Pytest MCP Server - AI-enhanced testing framework integration.

This package provides MCP (Model Context Protocol) server functionality for pytest,
enabling AI agents to access test results, track debugging progress, and generate
targeted debugging assistance.
"""

__version__ = "0.1.0"
__author__ = "Developer"
__email__ = "developer@example.com"

from .server import create_server
from .models import TestSession, TestCase, TestResult, FailureAnalysis

__all__ = [
    "create_server",
    "TestSession",
    "TestCase",
    "TestResult",
    "FailureAnalysis",
]