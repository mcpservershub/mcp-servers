"""Pytest configuration and fixtures"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio


@pytest.fixture
def mock_executor():
    """Mock command executor"""
    with patch('inspektor_mcp.utils.executor.CommandExecutor') as mock:
        executor = mock.return_value
        executor.execute = AsyncMock()
        executor.execute_streaming = AsyncMock()
        yield executor


@pytest.fixture
def sample_container_data():
    """Sample container data for testing"""
    return {
        "id": "abc123",
        "name": "test-container",
        "runtime": "docker",
        "state": "running",
        "namespace": "default",
        "pid": 12345
    }


@pytest.fixture
def sample_process_data():
    """Sample process data for testing"""
    return {
        "pid": 1234,
        "ppid": 1,
        "comm": "test-process",
        "uid": 1000,
        "gid": 1000,
        "container": "test-container"
    }


@pytest.fixture
def sample_network_event():
    """Sample network event for testing"""
    return {
        "timestamp": "2025-01-01T12:00:00Z",
        "pid": 5678,
        "comm": "curl",
        "container": "test-container",
        "protocol": "tcp",
        "src_addr": "10.0.0.1",
        "src_port": 45678,
        "dst_addr": "10.0.0.2",
        "dst_port": 80,
        "event_type": "connect"
    }