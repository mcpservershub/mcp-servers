"""Custom exceptions for the MCP Server"""


class InspektorMCPError(Exception):
    """Base exception for MCP Server errors"""
    pass


class IGNotFoundError(InspektorMCPError):
    """Inspektor-Gadget binary not found"""
    pass


class IGDaemonError(InspektorMCPError):
    """IG daemon connection/communication error"""
    pass


class ContainerNotFoundError(InspektorMCPError):
    """Specified container not found"""
    pass


class GadgetExecutionError(InspektorMCPError):
    """Gadget execution failed"""
    pass


class PermissionError(InspektorMCPError):
    """Insufficient permissions (need root/CAP_SYS_ADMIN)"""
    pass


class TimeoutError(InspektorMCPError):
    """Command execution timeout"""
    pass