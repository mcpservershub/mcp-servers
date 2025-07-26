#!/bin/bash
# Debug script to check Dependency Check installation in container

echo "=== Checking Dependency Check Installation ==="
echo "DEPENDENCY_CHECK_HOME: $DEPENDENCY_CHECK_HOME"
echo "PATH: $PATH"

echo -e "\n=== Checking /opt/dependency-check directory ==="
ls -la /opt/dependency-check/

echo -e "\n=== Checking bin directory ==="
ls -la /opt/dependency-check/bin/

echo -e "\n=== Checking if dependency-check.sh is executable ==="
file /opt/dependency-check/bin/dependency-check.sh
ls -la /opt/dependency-check/bin/dependency-check.sh

echo -e "\n=== Testing dependency-check command ==="
which dependency-check.sh || echo "dependency-check.sh not in PATH"

echo -e "\n=== Trying to run dependency-check ==="
/opt/dependency-check/bin/dependency-check.sh --version || echo "Failed to run dependency-check"

echo -e "\n=== Checking Java installation ==="
java -version

echo -e "\n=== Testing with a simple scan ==="
mkdir -p /tmp/test_project
echo '{"name": "test", "version": "1.0.0", "dependencies": {"lodash": "4.17.11"}}' > /tmp/test_project/package.json
cd /tmp/test_project
/opt/dependency-check/bin/dependency-check.sh --scan . --format JSON --out /tmp/test_output --project test || echo "Scan failed"

echo -e "\n=== Checking output ==="
ls -la /tmp/test_output/