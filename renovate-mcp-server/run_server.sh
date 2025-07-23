#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
exec python -m renovate_mcp.server