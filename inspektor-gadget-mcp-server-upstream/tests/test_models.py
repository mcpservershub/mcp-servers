"""Test Pydantic models"""

import pytest
from pydantic import ValidationError

from inspektor_mcp.models import (
    ListContainersRequest,
    TraceExecRequest,
    TraceNetworkRequest,
    ProfileCPURequest,
    Target,
    Runtime,
    OutputFormat,
)


class TestListContainersRequest:
    def test_valid_request(self):
        """Test valid list containers request"""
        req = ListContainersRequest(
            runtime=Runtime.DOCKER,
            namespace="default",
            containername="test",
            output_format=OutputFormat.JSON
        )
        assert req.runtime == Runtime.DOCKER
        assert req.namespace == "default"
        assert req.containername == "test"
        assert req.output_format == OutputFormat.JSON
    
    def test_defaults(self):
        """Test default values"""
        req = ListContainersRequest()
        assert req.runtime == Runtime.ALL
        assert req.output_format == OutputFormat.JSON
        assert req.namespace is None
        assert req.containername is None


class TestTraceExecRequest:
    def test_valid_container_request(self):
        """Test valid trace exec request for container"""
        req = TraceExecRequest(
            target=Target.CONTAINER,
            container_name="test-container",
            duration=30,
            follow_fork=True
        )
        assert req.target == Target.CONTAINER
        assert req.container_name == "test-container"
        assert req.duration == 30
        assert req.follow_fork is True
    
    def test_valid_host_request(self):
        """Test valid trace exec request for host"""
        req = TraceExecRequest(
            target=Target.HOST,
            duration=60,
            filter_uid=1000,
            filter_comm="bash"
        )
        assert req.target == Target.HOST
        assert req.duration == 60
        assert req.filter_uid == 1000
        assert req.filter_comm == "bash"
    
    def test_container_without_name(self):
        """Test that container target requires container_name"""
        with pytest.raises(ValidationError) as exc_info:
            TraceExecRequest(
                target=Target.CONTAINER,
                duration=30
            )
        assert "container_name is required" in str(exc_info.value)
    
    def test_duration_validation(self):
        """Test duration bounds validation"""
        # Too short
        with pytest.raises(ValidationError):
            TraceExecRequest(
                target=Target.HOST,
                duration=0
            )
        
        # Too long
        with pytest.raises(ValidationError):
            TraceExecRequest(
                target=Target.HOST,
                duration=301
            )
        
        # Valid range
        req = TraceExecRequest(target=Target.HOST, duration=150)
        assert req.duration == 150


class TestProfileCPURequest:
    def test_valid_container_profile(self):
        """Test valid CPU profile request for container"""
        req = ProfileCPURequest(
            target=Target.CONTAINER,
            container_name="test-app",
            duration=60,
            frequency=99,
            output_format="flamegraph"
        )
        assert req.target == Target.CONTAINER
        assert req.container_name == "test-app"
        assert req.duration == 60
        assert req.frequency == 99
        assert req.output_format == "flamegraph"
    
    def test_valid_pid_profile(self):
        """Test valid CPU profile request for PID"""
        req = ProfileCPURequest(
            target=Target.PID,
            pid=12345,
            duration=30,
            frequency=50
        )
        assert req.target == Target.PID
        assert req.pid == 12345
        assert req.duration == 30
        assert req.frequency == 50
    
    def test_pid_without_value(self):
        """Test that PID target requires pid value"""
        with pytest.raises(ValidationError) as exc_info:
            ProfileCPURequest(
                target=Target.PID,
                duration=30
            )
        assert "pid is required" in str(exc_info.value)
    
    def test_frequency_validation(self):
        """Test frequency bounds validation"""
        # Too low
        with pytest.raises(ValidationError):
            ProfileCPURequest(
                target=Target.HOST,
                frequency=0
            )
        
        # Too high
        with pytest.raises(ValidationError):
            ProfileCPURequest(
                target=Target.HOST,
                frequency=1001
            )
        
        # Valid range
        req = ProfileCPURequest(target=Target.HOST, frequency=500)
        assert req.frequency == 500