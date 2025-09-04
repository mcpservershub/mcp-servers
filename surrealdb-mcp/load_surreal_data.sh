#!/bin/bash

# SurrealDB Test Data Loader
# Uses proper SurrealQL syntax

# Configuration
SURREAL_URL="${SURREAL_URL:-http://localhost:8000}"
SURREAL_USER="${SURREAL_USER:-root}"
SURREAL_PASS="${SURREAL_PASS:-root}"

echo "================================================"
echo "SurrealDB Test Data Loader"
echo "================================================"
echo ""
echo "Configuration:"
echo "  URL: $SURREAL_URL"
echo "  User: $SURREAL_USER"
echo ""

# Check if SurrealDB is running
echo "Checking SurrealDB connection..."
if ! curl -s -f "$SURREAL_URL/health" > /dev/null 2>&1; then
    echo "Error: Cannot connect to SurrealDB at $SURREAL_URL"
    echo "Please ensure SurrealDB is running:"
    echo "  surreal start --user root --pass root"
    exit 1
fi

echo "✓ SurrealDB is running"
echo ""

# Method 1: Using surreal CLI (preferred)
if command -v surreal &> /dev/null; then
    echo "Using surreal CLI to import data..."
    
    surreal import \
        --conn "$SURREAL_URL" \
        --user "$SURREAL_USER" \
        --pass "$SURREAL_PASS" \
        --ns test \
        --db test \
        surrealdb_test_data.surql
    
    if [ $? -eq 0 ]; then
        echo "✓ Test data loaded successfully!"
    else
        echo "⚠ Import failed, trying HTTP method..."
    fi
else
    echo "surreal CLI not found, using HTTP API..."
fi

# Method 2: Using HTTP API with proper headers
echo ""
echo "Loading data via HTTP API..."

# Read the file content
SQL_CONTENT=$(cat surrealdb_test_data.surql)

# Send the request
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -X POST \
    -u "${SURREAL_USER}:${SURREAL_PASS}" \
    -H "Accept: application/json" \
    -H "NS: test" \
    -H "DB: test" \
    --data-binary "$SQL_CONTENT" \
    "$SURREAL_URL/sql")

# Extract status code
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✓ Data loaded successfully via HTTP!"
else
    echo "✗ Failed to load data (HTTP $HTTP_STATUS)"
    echo "Response:"
    echo "$RESPONSE" | head -n -1
    exit 1
fi

echo ""
echo "================================================"
echo "Verifying Data"
echo "================================================"
echo ""

# Test queries
echo "Testing user records..."
USER_COUNT=$(curl -s -X POST \
    -u "${SURREAL_USER}:${SURREAL_PASS}" \
    -H "Accept: application/json" \
    -H "NS: test" \
    -H "DB: test" \
    --data "SELECT * FROM user;" \
    "$SURREAL_URL/sql" | grep -o "user:" | wc -l)

echo "✓ Found $USER_COUNT user records"

echo "Testing post records..."
POST_COUNT=$(curl -s -X POST \
    -u "${SURREAL_USER}:${SURREAL_PASS}" \
    -H "Accept: application/json" \
    -H "NS: test" \
    -H "DB: test" \
    --data "SELECT * FROM post;" \
    "$SURREAL_URL/sql" | grep -o "post:" | wc -l)

echo "✓ Found $POST_COUNT post records"

echo "Testing product records..."
PRODUCT_COUNT=$(curl -s -X POST \
    -u "${SURREAL_USER}:${SURREAL_PASS}" \
    -H "Accept: application/json" \
    -H "NS: test" \
    -H "DB: test" \
    --data "SELECT * FROM product;" \
    "$SURREAL_URL/sql" | grep -o "product:" | wc -l)

echo "✓ Found $PRODUCT_COUNT product records"

echo ""
echo "================================================"
echo "Sample Queries to Test"
echo "================================================"
echo ""
echo "1. Get all users:"
echo "   SELECT * FROM user;"
echo ""
echo "2. Get posts with author info:"
echo "   SELECT *, author.name as author_name FROM post;"
echo ""
echo "3. Get user relationships:"
echo "   SELECT * FROM user:john->follows->user;"
echo ""
echo "4. Get products by category:"
echo "   SELECT * FROM product WHERE category = 'electronics';"
echo ""
echo "5. Get orders:"
echo "   SELECT * FROM \`order\`;"
echo ""
echo "================================================"
echo "Testing with SurrealMCP"
echo "================================================"
echo ""
echo "1. Start SurrealMCP:"
echo ""
echo "   # Standalone (if built locally):"
echo "   surrealmcp start \\"
echo "     --endpoint ws://localhost:8000/rpc \\"
echo "     --ns test --db test \\"
echo "     --user root --pass root"
echo ""
echo "   # Using Docker:"
echo "   docker run --rm -i --network host \\"
echo "     surrealmcp:local start \\"
echo "     --endpoint ws://localhost:8000/rpc \\"
echo "     --ns test --db test \\"
echo "     --user root --pass root"
echo ""
echo "2. Test with MCP Inspector:"
echo ""
echo "   npx @modelcontextprotocol/inspector \\"
echo "     docker run --rm -i --network host \\"
echo "     surrealmcp:local start \\"
echo "     --endpoint ws://localhost:8000/rpc \\"
echo "     --ns test --db test \\"
echo "     --user root --pass root"
echo ""
echo "✓ Test database is ready!"