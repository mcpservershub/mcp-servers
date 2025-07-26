#!/bin/bash
# Test script to verify container setup

echo "=== Testing Dependency Check in Container ==="

# Test 1: Check if binary exists
echo -e "\n1. Checking if dependency-check.sh exists:"
if [ -f "/opt/dependency-check/bin/dependency-check.sh" ]; then
    echo "✓ Binary exists"
    ls -la /opt/dependency-check/bin/dependency-check.sh
else
    echo "✗ Binary NOT found"
fi

# Test 2: Check Java
echo -e "\n2. Checking Java installation:"
java -version 2>&1 || echo "✗ Java not found"

# Test 3: Try to run dependency-check
echo -e "\n3. Running dependency-check --version:"
/opt/dependency-check/bin/dependency-check.sh --version 2>&1 || echo "✗ Failed to run"

# Test 4: Create a test project and scan
echo -e "\n4. Creating test project:"
mkdir -p /tmp/test_project
cat > /tmp/test_project/package.json << EOF
{
  "name": "test-vulnerable",
  "version": "1.0.0",
  "dependencies": {
    "lodash": "4.17.11"
  }
}
EOF

echo "Test project created with vulnerable lodash version"

# Test 5: Run actual scan
echo -e "\n5. Running scan on test project:"
/opt/dependency-check/bin/dependency-check.sh \
    --scan /tmp/test_project \
    --format JSON \
    --out /tmp/test_output \
    --project test \
    --log /tmp/dc.log \
    2>&1

echo -e "\n6. Checking output:"
ls -la /tmp/test_output/ 2>&1 || echo "No output directory"

echo -e "\n7. Dependency Check log:"
cat /tmp/dc.log 2>&1 | head -50 || echo "No log file"