"""Pydantic models for type validation"""

from typing import Optional, List, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class Runtime(str, Enum):
    DOCKER = "docker"
    CONTAINERD = "containerd"
    CRIO = "crio"
    PODMAN = "podman"
    ALL = "all"


class OutputFormat(str, Enum):
    JSON = "json"
    TABLE = "table"
    YAML = "yaml"


class Target(str, Enum):
    HOST = "host"
    CONTAINER = "container"
    PID = "pid"


class TraceType(str, Enum):
    DNS = "dns"
    TCP = "tcp"
    BIND = "bind"
    SSL = "ssl"
    SNI = "sni"
    ALL = "all"


class ResourceType(str, Enum):
    PROCESS = "process"
    FILE = "file"
    TCP = "tcp"
    BLOCKIO = "blockio"
    ALL = "all"


class SnapshotType(str, Enum):
    PROCESS = "process"
    SOCKET = "socket"
    ALL = "all"


class RunGadgetRequest(BaseModel):
    """Request model for running arbitrary gadgets"""
    
    gadget_name: str = Field(
        description="Gadget name - can be short name (e.g., 'trace_open') or full image URL (e.g., 'ghcr.io/inspektor-gadget/gadget/trace_exec:v0.43.0')"
    )
    
    container_name: Union[str, None] = Field(
        default=None,
        description="[OPTIONAL] Container name to monitor. If not provided, monitors the host"
    )
    
    args: List[str] = Field(
        default_factory=list,
        description="[OPTIONAL] Additional arguments to pass to the gadget"
    )
    
    timeout_seconds: int = Field(
        default=120,
        ge=1,
        le=600,
        description="[OPTIONAL] Timeout for gadget execution in seconds (1-600, default: 120)"
    )
    
    @field_validator('gadget_name')
    def validate_gadget_name(cls, v):
        if not v or v.strip() == "":
            raise ValueError("gadget_name cannot be empty")
        return v.strip()


class AdviceType(str, Enum):
    NETWORKPOLICY = "networkpolicy"
    SECCOMP = "seccomp"
    ALL = "all"


# Request models for each tool
class ListContainersRequest(BaseModel):
    runtime: Runtime = Field(
        default=Runtime.ALL,
        description="Container runtime to query. Options: docker, containerd, crio, podman, all"
    )
    namespace: Union[str, None] = Field(
        default=None,
        description="[OPTIONAL] Namespace for containerd runtime (default: k8s.io)"
    )
    containername: Union[str, None] = Field(
        default=None,
        description="[OPTIONAL] Filter by specific container name"
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.JSON,
        description="Output format. Options: json, table"
    )


class TraceExecRequest(BaseModel):
    target: Target = Field(
        default=Target.HOST,
        description="Trace target. Options: host (monitor Linux host), container (monitor specific container)"
    )
    container_name: Union[str, None] = Field(
        default=None,
        description="[OPTIONAL] Container name to monitor. If not provided, monitors the host. Required only when target='container'"
    )
    duration: int = Field(
        default=10,
        ge=1,
        le=300,
        description="Duration to trace in seconds (1-300)"
    )
    filter_uid: Union[int, None] = Field(
        default=None,
        description="[OPTIONAL] Filter by user ID (UID)"
    )
    filter_comm: Union[str, None] = Field(
        default=None,
        description="[OPTIONAL] Filter by command name"
    )
    follow_fork: bool = Field(
        default=True,
        description="Follow forked processes"
    )
    
    @model_validator(mode='after')
    def validate_container_name(self):
        if self.target == Target.CONTAINER and not self.container_name:
            raise ValueError("container_name is required when target is 'container'")
        return self


class TraceNetworkRequest(BaseModel):
    trace_type: TraceType = Field(
        default=TraceType.TCP,
        description="Network trace type. Options: dns, tcp, bind, ssl, sni, all"
    )
    container_name: Union[str, None] = Field(
        default=None,
        description="[OPTIONAL] Container name to monitor. If not provided, monitors the host"
    )
    duration: int = Field(
        default=10,
        ge=1,
        le=300,
        description="Duration to trace in seconds (1-300)"
    )
    filter_port: Union[int, None] = Field(
        default=None,
        ge=1,
        le=65535,
        description="[OPTIONAL] Filter by port number (1-65535)"
    )
    filter_protocol: Literal["tcp", "udp"] = Field(
        default="tcp",
        description="Protocol to filter. Options: tcp, udp"
    )
    show_drops: bool = Field(
        default=False,
        description="Show dropped packets/connections"
    )
    show_retransmissions: bool = Field(
        default=False,
        description="Show TCP retransmissions"
    )


class TraceFilesystemRequest(BaseModel):
    trace_type: Literal["open", "mount", "fsslower"] = Field(
        default="open",
        description="Filesystem trace type. Options: open (file opens), mount (mount operations), fsslower (slow I/O)"
    )
    container_name: Union[str, None] = Field(
        default=None,
        description="[OPTIONAL] Container name to monitor. If not provided, monitors the host"
    )
    duration: int = Field(
        default=10,
        ge=1,
        le=300,
        description="Duration to trace in seconds (1-300)"
    )
    filter_path: Union[str, None] = Field(
        default=None,
        description="[OPTIONAL] Filter by file path pattern"
    )
    min_latency_ms: Union[int, None] = Field(
        default=None,
        ge=0,
        description="[OPTIONAL] Minimum I/O latency in milliseconds (for fsslower)"
    )


class ProfileCPURequest(BaseModel):
    target: Target = Field(
        default=Target.HOST,
        description="Profile target. Options: host (profile Linux host), container (profile specific container), pid (profile specific process)"
    )
    container_name: Union[str, None] = Field(
        default=None,
        description="[OPTIONAL] Container name to profile. Required only when target='container'"
    )
    pid: Union[int, None] = Field(
        default=None,
        description="[OPTIONAL] Process ID to profile. Required only when target='pid'"
    )
    duration: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Duration to profile in seconds (1-300)"
    )
    frequency: int = Field(
        default=99,
        ge=1,
        le=1000,
        description="Sampling frequency in Hz (1-1000)"
    )
    output_format: Literal["flamegraph", "raw", "folded"] = Field(
        default="flamegraph",
        description="Output format. Options: flamegraph, raw, folded"
    )
    
    @model_validator(mode='after')
    def validate_fields(self):
        if self.target == Target.CONTAINER and not self.container_name:
            raise ValueError("container_name is required when target is 'container'")
        if self.target == Target.PID and not self.pid:
            raise ValueError("pid is required when target is 'pid'")
        return self


class ProfileIORequest(BaseModel):
    profile_type: Literal["blockio", "tcprtt"] = Field(
        default="blockio",
        description="I/O profile type. Options: blockio (block I/O), tcprtt (TCP round-trip time)"
    )
    container_name: Union[str, None] = Field(
        default=None,
        description="[OPTIONAL] Container name to profile. If not provided, profiles the host"
    )
    duration: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Duration to profile in seconds (1-300)"
    )


class SnapshotSystemRequest(BaseModel):
    snapshot_type: SnapshotType = Field(
        default=SnapshotType.PROCESS,
        description="Snapshot type. Options: process, socket, all"
    )
    container_name: Union[str, None] = Field(
        default=None,
        description="[OPTIONAL] Container name to snapshot. If not provided, snapshots the host"
    )
    include_threads: bool = Field(
        default=False,
        description="Include thread information (for process snapshots)"
    )
    include_tcp: bool = Field(
        default=True,
        description="Include TCP sockets (for socket snapshots)"
    )
    include_udp: bool = Field(
        default=True,
        description="Include UDP sockets (for socket snapshots)"
    )
    include_unix: bool = Field(
        default=False,
        description="Include Unix domain sockets (for socket snapshots)"
    )


class TopResourcesRequest(BaseModel):
    resource_type: ResourceType = Field(
        default=ResourceType.PROCESS,
        description="Resource type to monitor. Options: process, file, tcp, blockio, all"
    )
    container_name: Union[str, None] = Field(
        default=None,
        description="[OPTIONAL] Container name to monitor. If not provided, monitors the host"
    )
    interval: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Update interval in seconds (1-10)"
    )
    max_rows: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of rows to display (1-50)"
    )
    sort_by: Literal["cpu", "memory", "io", "pid"] = Field(
        default="cpu",
        description="Sort by field. Options: cpu, memory, io, pid"
    )


class AdviseSecurityRequest(BaseModel):
    advice_type: AdviceType = Field(
        default=AdviceType.ALL,
        description="Security advice type. Options: networkpolicy, seccomp, all"
    )
    container_name: str = Field(
        description="[REQUIRED] Container name to analyze for security recommendations"
    )
    duration: int = Field(
        default=60,
        ge=10,
        le=600,
        description="Observation duration in seconds (10-600)"
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.YAML,
        description="Output format. Options: yaml, json"
    )


class AnalyzeDeadlockRequest(BaseModel):
    container_name: Union[str, None] = Field(
        default=None,
        description="[OPTIONAL] Container name to analyze. If not provided, analyzes the host"
    )
    pid: Union[int, None] = Field(
        default=None,
        description="[OPTIONAL] Specific process ID to analyze"
    )
    duration: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Analysis duration in seconds (1-300)"
    )
    stack_depth: int = Field(
        default=20,
        ge=1,
        le=127,
        description="Stack trace depth (1-127)"
    )


# Response models
class CommandResult(BaseModel):
    success: bool
    data: Optional[Any] = None  # Can be dict, list, string, etc.
    error: Optional[str] = None
    command: Optional[str] = None
    duration_ms: Optional[float] = None


class ContainerInfo(BaseModel):
    id: str
    name: str
    runtime: str
    state: str
    namespace: Optional[str] = None
    pid: Optional[int] = None


class ProcessInfo(BaseModel):
    pid: int
    ppid: int
    comm: str
    uid: Optional[int] = None
    gid: Optional[int] = None
    container: Optional[str] = None
    timestamp: Optional[str] = None


class NetworkEvent(BaseModel):
    timestamp: str
    pid: int
    comm: str
    container: Optional[str] = None
    protocol: str
    src_addr: Optional[str] = None
    src_port: Optional[int] = None
    dst_addr: Optional[str] = None
    dst_port: Optional[int] = None
    event_type: Optional[str] = None