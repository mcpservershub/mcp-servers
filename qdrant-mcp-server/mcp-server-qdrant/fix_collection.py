#!/usr/bin/env python3
"""
Fix script to recreate the Qdrant collection with the correct vector field name
that matches the MCP server's expectations.
"""

import sys
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

def fix_collection(
    host: str = "localhost",
    port: int = 6333,
    collection_name: str = "test-collection",
    vector_field_name: str = "fast-all-minilm-l6-v2",
    vector_size: int = 384
):
    """
    Recreate the collection with the correct vector field name.
    """
    print(f"🔧 Fixing collection '{collection_name}' with vector field '{vector_field_name}'")
    
    try:
        # Connect to Qdrant
        client = QdrantClient(host=host, port=port)
        
        # Check if collection exists
        collections = client.get_collections().collections
        collection_exists = any(c.name == collection_name for c in collections)
        
        if collection_exists:
            print(f"📦 Deleting existing collection '{collection_name}'...")
            client.delete_collection(collection_name)
            print("✅ Collection deleted")
        
        # Create collection with named vector field
        print(f"📦 Creating collection with vector field '{vector_field_name}'...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                vector_field_name: VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            }
        )
        print("✅ Collection created successfully")
        
        # Verify the collection
        info = client.get_collection(collection_name)
        print(f"📊 Collection info:")
        print(f"   - Status: {info.status}")
        print(f"   - Points count: {info.points_count}")
        print(f"   - Vector config: {info.config.params.vectors}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 Qdrant Collection Fix Script")
    print("=" * 50)
    
    # Check if Qdrant is running
    try:
        client = QdrantClient(host="localhost", port=6333)
        client.get_collections()
        print("✅ Connected to Qdrant")
    except Exception as e:
        print(f"❌ Cannot connect to Qdrant: {e}")
        print("   Please ensure Qdrant is running: docker-compose up -d")
        sys.exit(1)
    
    # Fix the collection
    if fix_collection():
        print("\n✅ Collection fixed successfully!")
        print("\n📝 Next steps:")
        print("1. Reload mock data with the fixed loader:")
        print("   python3 load_mock_data_fixed.py")
        print("\n2. Start MCP server:")
        print("   uvx mcp-server-qdrant")
        print("\n3. Test with MCP Inspector:")
        print("   npx @modelcontextprotocol/inspector uvx mcp-server-qdrant")
    else:
        print("\n❌ Failed to fix collection")
        sys.exit(1)

if __name__ == "__main__":
    main()