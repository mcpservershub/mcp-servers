"""Registry of available gadget images"""

# Gadget image registry for ig v0.43.0
# Format: ghcr.io/inspektor-gadget/gadget/GADGET_NAME:v0.43.0

GADGET_IMAGES = {
    # Tracing gadgets
    "trace_exec": "ghcr.io/inspektor-gadget/gadget/trace_exec:v0.43.0",
    "trace_open": "ghcr.io/inspektor-gadget/gadget/trace_open:v0.43.0",
    "trace_mount": "ghcr.io/inspektor-gadget/gadget/trace_mount:v0.43.0",
    "trace_tcp": "ghcr.io/inspektor-gadget/gadget/trace_tcp:v0.43.0",
    "trace_tcpconnect": "ghcr.io/inspektor-gadget/gadget/trace_tcpconnect:v0.43.0",
    "trace_tcpdrop": "ghcr.io/inspektor-gadget/gadget/trace_tcpdrop:v0.43.0",
    "trace_tcpretrans": "ghcr.io/inspektor-gadget/gadget/trace_tcpretrans:v0.43.0",
    "trace_dns": "ghcr.io/inspektor-gadget/gadget/trace_dns:v0.43.0",
    "trace_bind": "ghcr.io/inspektor-gadget/gadget/trace_bind:v0.43.0",
    "trace_ssl": "ghcr.io/inspektor-gadget/gadget/trace_ssl:v0.43.0",
    "trace_sni": "ghcr.io/inspektor-gadget/gadget/trace_sni:v0.43.0",
    "trace_signal": "ghcr.io/inspektor-gadget/gadget/trace_signal:v0.43.0",
    "trace_capabilities": "ghcr.io/inspektor-gadget/gadget/trace_capabilities:v0.43.0",
    "trace_fsslower": "ghcr.io/inspektor-gadget/gadget/trace_fsslower:v0.43.0",
    "trace_oomkill": "ghcr.io/inspektor-gadget/gadget/trace_oomkill:v0.43.0",
    
    # Profiling gadgets
    "profile_cpu": "ghcr.io/inspektor-gadget/gadget/profile_cpu:v0.43.0",
    "profile_blockio": "ghcr.io/inspektor-gadget/gadget/profile_blockio:v0.43.0",
    "profile_tcprtt": "ghcr.io/inspektor-gadget/gadget/profile_tcprtt:v0.43.0",
    
    # Top gadgets
    "top_process": "ghcr.io/inspektor-gadget/gadget/top_process:v0.43.0",
    "top_file": "ghcr.io/inspektor-gadget/gadget/top_file:v0.43.0",
    "top_tcp": "ghcr.io/inspektor-gadget/gadget/top_tcp:v0.43.0",
    "top_blockio": "ghcr.io/inspektor-gadget/gadget/top_blockio:v0.43.0",
    
    # Snapshot gadgets
    "snapshot_process": "ghcr.io/inspektor-gadget/gadget/snapshot_process:v0.43.0",
    "snapshot_socket": "ghcr.io/inspektor-gadget/gadget/snapshot_socket:v0.43.0",
    
    # Advisory gadgets
    "advise_networkpolicy": "ghcr.io/inspektor-gadget/gadget/advise_networkpolicy:v0.43.0",
    "advise_seccomp": "ghcr.io/inspektor-gadget/gadget/advise_seccomp:v0.43.0",
    
    # Audit gadgets
    "audit_seccomp": "ghcr.io/inspektor-gadget/gadget/audit_seccomp:v0.43.0",
    
    # Other gadgets
    "deadlock": "ghcr.io/inspektor-gadget/gadget/deadlock:v0.43.0",
    "fsnotify": "ghcr.io/inspektor-gadget/gadget/fsnotify:v0.43.0",
    "traceloop": "ghcr.io/inspektor-gadget/gadget/traceloop:v0.43.0",
}