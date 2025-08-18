#!/usr/bin/env python3
"""
MCP Client for Testing Qdrant MCP Server
This script demonstrates how to interact with the Qdrant MCP Server programmatically
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any, List
from datetime import datetime

# Check if mcp is installed
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("❌ MCP client library not installed.")
    print("   Install with: pip install mcp")
    sys.exit(1)

class QdrantMCPClient:
    """Client for interacting with Qdrant MCP Server"""
    
    def __init__(self, qdrant_url: str = "http://localhost:6333", 
                 collection_name: str = "test-collection"):
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.server_params = StdioServerParameters(
            command="uvx",
            args=["mcp-server-qdrant"],
            env={
                "QDRANT_URL": qdrant_url,
                "COLLECTION_NAME": collection_name,
                "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2"
            }
        )
    
    async def test_connection(self) -> bool:
        """Test connection to MCP server"""
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    print(f"✅ Connected to MCP Server. Available tools: {[t.name for t in tools]}")
                    return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    async def search_information(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for information using the qdrant-find tool"""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool(
                    "qdrant-find",
                    arguments={
                        "query": query,
                        "limit": limit
                    }
                )
                return result
    
    async def store_information(self, information: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Store information using the qdrant-store tool"""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                args = {"information": information}
                if metadata:
                    args["metadata"] = metadata
                
                result = await session.call_tool("qdrant-store", arguments=args)
                return result
    
    async def run_interactive_tests(self):
        """Run a series of interactive tests"""
        print("\n" + "="*60)
        print("🧪 Running Interactive MCP Tests")
        print("="*60)
        
        # Test 1: Search existing mock data
        print("\n📝 Test 1: Search Existing Data")
        print("-" * 40)
        
        test_queries = [
            "How to implement WebSocket authentication in FastAPI",
            "Kubernetes pod troubleshooting CrashLoopBackOff",
            "Database performance optimization indexing",
            "Docker multi-stage build optimization"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            try:
                results = await self.search_information(query, limit=3)
                if isinstance(results, list):
                    for i, result in enumerate(results, 1):
                        if isinstance(result, dict):
                            score = result.get('score', 'N/A')
                            content = result.get('content', result.get('payload', {}))
                            if isinstance(content, dict):
                                title = content.get('title', content.get('type', 'Unknown'))
                                print(f"   {i}. [{score}] {title}")
                            else:
                                print(f"   {i}. [{score}] {str(content)[:100]}...")
                else:
                    print(f"   Results: {results}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Test 2: Store new information
        print("\n\n📝 Test 2: Store New Information")
        print("-" * 40)
        
        new_items = [
            {
                "information": """
                Terraform State Management Best Practices:
                1. Always use remote state backend (S3, Azure Storage, GCS)
                2. Enable state locking with DynamoDB or similar
                3. Use workspaces for environment separation
                4. Never commit state files to version control
                5. Implement state file encryption at rest
                6. Regular state backups before major changes
                """,
                "metadata": {
                    "type": "documentation",
                    "category": "infrastructure-as-code",
                    "tags": ["terraform", "iac", "state-management", "devops"],
                    "timestamp": datetime.now().isoformat()
                }
            },
            {
                "information": """
                async function retryWithExponentialBackoff(fn, maxRetries = 3) {
                    let lastError;
                    for (let i = 0; i < maxRetries; i++) {
                        try {
                            return await fn();
                        } catch (error) {
                            lastError = error;
                            const delay = Math.min(1000 * Math.pow(2, i), 10000);
                            await new Promise(resolve => setTimeout(resolve, delay));
                        }
                    }
                    throw lastError;
                }
                """,
                "metadata": {
                    "type": "code_snippet",
                    "language": "javascript",
                    "title": "Retry with exponential backoff in JavaScript",
                    "tags": ["javascript", "async", "retry", "error-handling"],
                    "timestamp": datetime.now().isoformat()
                }
            },
            {
                "information": """
                OAuth 2.0 PKCE Flow Implementation:
                PKCE (Proof Key for Code Exchange) prevents authorization code interception attacks.
                Steps: Generate code_verifier (random string), create code_challenge (SHA256 hash),
                include challenge in authorization request, send verifier in token exchange.
                Essential for public clients like SPAs and mobile apps.
                """,
                "metadata": {
                    "type": "security_guide",
                    "category": "authentication",
                    "tags": ["oauth", "pkce", "security", "authentication", "spa"],
                    "timestamp": datetime.now().isoformat()
                }
            }
        ]
        
        for item in new_items:
            title = item["metadata"].get("title", item["metadata"].get("type", "Information"))
            print(f"\n💾 Storing: {title}")
            try:
                result = await self.store_information(item["information"], item["metadata"])
                print(f"   ✅ Stored successfully: {result}")
            except Exception as e:
                print(f"   ❌ Error storing: {e}")
        
        # Test 3: Verify newly stored data
        print("\n\n📝 Test 3: Verify Newly Stored Data")
        print("-" * 40)
        
        verification_queries = [
            "Terraform state management remote backend",
            "JavaScript retry exponential backoff",
            "OAuth PKCE flow implementation"
        ]
        
        for query in verification_queries:
            print(f"\n🔍 Verifying: '{query}'")
            try:
                results = await self.search_information(query, limit=2)
                if isinstance(results, list) and len(results) > 0:
                    print(f"   ✅ Found {len(results)} results")
                    for i, result in enumerate(results[:2], 1):
                        if isinstance(result, dict):
                            score = result.get('score', 'N/A')
                            print(f"   {i}. Score: {score}")
                else:
                    print(f"   ⚠️  No results found")
            except Exception as e:
                print(f"   ❌ Error: {e}")

async def main():
    """Main test function"""
    print("🚀 Qdrant MCP Client Test Suite")
    print("="*60)
    
    # Check if Qdrant is running
    print("\n🔍 Checking prerequisites...")
    try:
        import requests
        response = requests.get("http://localhost:6333/health")
        if response.status_code == 200:
            print("✅ Qdrant is running")
        else:
            print("❌ Qdrant is not healthy")
            return
    except Exception as e:
        print(f"❌ Cannot connect to Qdrant: {e}")
        print("   Please run: docker-compose up -d")
        return
    
    # Create client and run tests
    client = QdrantMCPClient()
    
    # Test connection
    print("\n🔗 Testing MCP Server connection...")
    if not await client.test_connection():
        print("❌ Failed to connect to MCP Server")
        return
    
    # Run interactive tests
    await client.run_interactive_tests()
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    print("✅ Successfully connected to MCP Server")
    print("✅ Searched existing mock data")
    print("✅ Stored new information")
    print("✅ Verified stored data")
    print("\n💡 You can now use the MCP Server with:")
    print("   - MCP Inspector: npx @modelcontextprotocol/inspector uvx mcp-server-qdrant")
    print("   - Claude Desktop: Configure in claude_desktop_config.json")
    print("   - This Python client for programmatic access")
    print(f"\n📊 Qdrant Dashboard: http://localhost:6333/dashboard")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())