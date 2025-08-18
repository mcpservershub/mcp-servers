#!/usr/bin/env python3
"""
Quick fix to ensure data is in the correct collection name
"""

import sys
from qdrant_client import QdrantClient

def check_and_fix_collections():
    """Check which collections exist and provide guidance"""
    
    print("🔍 Checking Qdrant collections...")
    
    try:
        client = QdrantClient(host="localhost", port=6333)
        collections = client.get_collections().collections
        
        print("\n📦 Existing collections:")
        for col in collections:
            info = client.get_collection(col.name)
            print(f"  - {col.name}: {info.points_count} points")
        
        # Check for common collection name variations
        has_hyphen = any(c.name == "test-collection" for c in collections)
        has_underscore = any(c.name == "test_collection" for c in collections)
        
        if has_hyphen and not has_underscore:
            print("\n⚠️  Found 'test-collection' but MCP Inspector is looking for 'test_collection'")
            print("\n🔧 Two ways to fix this:\n")
            
            print("Option 1: Use the correct collection name in MCP Inspector:")
            print("  In the Inspector, use: test-collection (with hyphen)")
            print("")
            print("Option 2: Load data into test_collection (with underscore):")
            print("  Run: python3 load_mock_data_fixed.py --collection test_collection")
            
        elif has_underscore and not has_hyphen:
            print("\n✅ Collection 'test_collection' exists and should work!")
            
        elif has_hyphen and has_underscore:
            print("\n✅ Both collection variations exist")
            print("  Use 'test_collection' in MCP Inspector")
            
        else:
            print("\n⚠️  No test collections found. Please load mock data first:")
            print("  Run: python3 load_mock_data_fixed.py")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    check_and_fix_collections()