# Fixing MCP Timeout Issues

The timeout occurs because Dependency Check needs to download a large vulnerability database on first run, which can take 5-30 minutes.

## Solution 1: Pre-initialize the Database (Recommended)

Run this command ONCE before using MCP Inspector:

```bash
./init-database.sh
```

Or manually:

```bash
docker run --rm \
  -v dependency-check_dependency-check-data:/data/dependency-check \
  -e DEPENDENCY_CHECK_DATA=/data/dependency-check \
  santoshkal/dependency-check-mcp:cgr \
  /opt/dependency-check/bin/dependency-check.sh \
    --updateonly \
    --data /data/dependency-check
```

This downloads the database once. Future scans will be much faster (under 1 minute).

## Solution 2: Increase MCP Inspector Timeouts

In MCP Inspector settings:
- Request Timeout: `1800000` (30 minutes)
- Total Timeout: `1800000` (30 minutes)

## Solution 3: Use Direct Docker Command

For testing without MCP Inspector:

```bash
# Create output directory
mkdir -p output

# Run scan directly
docker run --rm \
  -v $(pwd):/workspace:ro \
  -v $(pwd)/output:/output \
  -v dependency-check_dependency-check-data:/data/dependency-check \
  -e DEPENDENCY_CHECK_DATA=/data/dependency-check \
  santoshkal/dependency-check-mcp:cgr \
  python3 -m src.dependency_check_mcp.server
```

Then use the scan_project tool with parameters.

## Why This Happens

1. **First Run**: Downloads ~2GB of vulnerability data
2. **MCP Timeout**: Default MCP timeout is shorter than download time
3. **No Progress Updates**: MCP doesn't see activity and times out

## Python Project Requirements

For Python projects to be scanned properly:
- Must have `requirements.txt` file
- Enable experimental analyzers: `"enable_experimental": true`
- Python dependencies are only partially supported

## Verified Working Example

After database initialization:

```json
{
  "path": "/workspace",
  "output_file": "/output/scan-results.json",
  "output_format": "JSON",
  "enable_experimental": true
}
```

This should complete in 10-60 seconds for most projects.