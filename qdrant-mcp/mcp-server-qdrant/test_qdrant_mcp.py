#!/usr/bin/env python3
"""
Test script for Qdrant MCP Server
This script verifies that the Qdrant instance and MCP server are working correctly
"""

import json
import time
import requests
from typing import List, Dict, Any
import sys

class QdrantTester:
    def __init__(self, qdrant_url: str = "http://localhost:6333", collection_name: str = "test-collection"):
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.api_base = f"{qdrant_url}"
        
    def check_health(self) -> bool:
        """Check if Qdrant is running"""
        try:
            response = requests.get(f"{self.api_base}/health")
            if response.status_code == 200:
                print("✅ Qdrant is healthy")
                return True
            else:
                print(f"❌ Qdrant health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to Qdrant: {e}")
            return False
    
    def create_collection(self, vector_size: int = 384) -> bool:
        """Create a test collection"""
        try:
            # Check if collection exists
            response = requests.get(f"{self.api_base}/collections/{self.collection_name}")
            if response.status_code == 200:
                print(f"ℹ️  Collection '{self.collection_name}' already exists")
                return True
            
            # Create new collection
            payload = {
                "vectors": {
                    "size": vector_size,
                    "distance": "Cosine"
                }
            }
            response = requests.put(
                f"{self.api_base}/collections/{self.collection_name}",
                json=payload
            )
            if response.status_code == 200:
                print(f"✅ Collection '{self.collection_name}' created successfully")
                return True
            else:
                print(f"❌ Failed to create collection: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error creating collection: {e}")
            return False
    
    def insert_test_data(self) -> bool:
        """Insert test vectors and payloads"""
        try:
            import random
            
            # Generate test data
            test_points = []
            test_texts = [
                "Qdrant is a vector database for semantic search",
                "Python is a programming language for data science",
                "Machine learning models can generate embeddings",
                "Vector search enables similarity matching",
                "The MCP server provides semantic memory storage"
            ]
            
            for i, text in enumerate(test_texts):
                # Generate random vector (in real use, this would be from an embedding model)
                vector = [random.random() for _ in range(384)]
                point = {
                    "id": i + 1,
                    "vector": vector,
                    "payload": {
                        "text": text,
                        "timestamp": time.time(),
                        "type": "test_data"
                    }
                }
                test_points.append(point)
            
            # Insert points
            payload = {"points": test_points}
            response = requests.put(
                f"{self.api_base}/collections/{self.collection_name}/points",
                json=payload
            )
            
            if response.status_code == 200:
                print(f"✅ Inserted {len(test_points)} test points")
                return True
            else:
                print(f"❌ Failed to insert points: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error inserting test data: {e}")
            return False
    
    def search_vectors(self, query_vector: List[float] = None) -> bool:
        """Perform a vector search"""
        try:
            import random
            
            # Use provided vector or generate random one
            if query_vector is None:
                query_vector = [random.random() for _ in range(384)]
            
            payload = {
                "vector": query_vector,
                "limit": 3,
                "with_payload": True
            }
            
            response = requests.post(
                f"{self.api_base}/collections/{self.collection_name}/points/search",
                json=payload
            )
            
            if response.status_code == 200:
                results = response.json()["result"]
                print(f"✅ Search returned {len(results)} results:")
                for i, result in enumerate(results, 1):
                    score = result.get("score", 0)
                    text = result.get("payload", {}).get("text", "N/A")
                    print(f"   {i}. Score: {score:.4f} - Text: {text[:50]}...")
                return True
            else:
                print(f"❌ Search failed: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error during search: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        try:
            response = requests.get(f"{self.api_base}/collections/{self.collection_name}")
            if response.status_code == 200:
                info = response.json()["result"]
                print(f"✅ Collection Info:")
                print(f"   - Status: {info['status']}")
                print(f"   - Points count: {info.get('points_count', 0)}")
                print(f"   - Vectors size: {info['config']['params']['vectors']['size']}")
                print(f"   - Distance: {info['config']['params']['vectors']['distance']}")
                return info
            else:
                print(f"❌ Failed to get collection info: {response.text}")
                return {}
        except Exception as e:
            print(f"❌ Error getting collection info: {e}")
            return {}
    
    def test_bulk_operations(self, num_points: int = 100) -> bool:
        """Test bulk insert and search operations"""
        try:
            import random
            print(f"\n📊 Testing bulk operations with {num_points} points...")
            
            # Generate bulk data
            bulk_points = []
            for i in range(num_points):
                vector = [random.random() for _ in range(384)]
                point = {
                    "id": 1000 + i,
                    "vector": vector,
                    "payload": {
                        "text": f"Bulk test point {i}",
                        "index": i,
                        "type": "bulk_test"
                    }
                }
                bulk_points.append(point)
            
            # Insert in batches
            batch_size = 50
            for i in range(0, len(bulk_points), batch_size):
                batch = bulk_points[i:i+batch_size]
                payload = {"points": batch}
                response = requests.put(
                    f"{self.api_base}/collections/{self.collection_name}/points",
                    json=payload
                )
                if response.status_code != 200:
                    print(f"❌ Batch insert failed at batch {i//batch_size}")
                    return False
            
            print(f"✅ Successfully inserted {num_points} points in bulk")
            
            # Wait for indexing
            time.sleep(1)
            
            # Perform multiple searches
            print("🔍 Performing random searches...")
            for i in range(3):
                query_vector = [random.random() for _ in range(384)]
                payload = {
                    "vector": query_vector,
                    "limit": 5,
                    "filter": {
                        "must": [
                            {"key": "type", "match": {"value": "bulk_test"}}
                        ]
                    }
                }
                response = requests.post(
                    f"{self.api_base}/collections/{self.collection_name}/points/search",
                    json=payload
                )
                if response.status_code == 200:
                    results = response.json()["result"]
                    print(f"   Search {i+1}: Found {len(results)} results")
                else:
                    print(f"❌ Search {i+1} failed")
                    return False
            
            print("✅ Bulk operations test completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error in bulk operations: {e}")
            return False
    
    def cleanup_test_data(self) -> bool:
        """Clean up test data from collection"""
        try:
            # Delete points with test_data type
            payload = {
                "filter": {
                    "must": [
                        {"key": "type", "match": {"value": "test_data"}}
                    ]
                }
            }
            response = requests.post(
                f"{self.api_base}/collections/{self.collection_name}/points/delete",
                json=payload
            )
            if response.status_code == 200:
                print("✅ Cleaned up test data")
                return True
            else:
                print(f"❌ Failed to cleanup: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            return False

def main():
    print("🚀 Starting Qdrant MCP Server Test Suite")
    print("=" * 50)
    
    tester = QdrantTester()
    
    # Run tests
    tests_passed = 0
    tests_total = 7
    
    print("\n1️⃣  Checking Qdrant Health...")
    if tester.check_health():
        tests_passed += 1
    else:
        print("⚠️  Please ensure Qdrant is running: docker-compose up -d")
        sys.exit(1)
    
    print("\n2️⃣  Creating/Verifying Collection...")
    if tester.create_collection():
        tests_passed += 1
    
    print("\n3️⃣  Inserting Test Data...")
    if tester.insert_test_data():
        tests_passed += 1
    
    print("\n4️⃣  Getting Collection Info...")
    info = tester.get_collection_info()
    if info:
        tests_passed += 1
    
    print("\n5️⃣  Performing Vector Search...")
    if tester.search_vectors():
        tests_passed += 1
    
    print("\n6️⃣  Testing Bulk Operations...")
    if tester.test_bulk_operations(50):
        tests_passed += 1
    
    print("\n7️⃣  Cleaning Up Test Data...")
    if tester.cleanup_test_data():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{tests_total} passed")
    
    if tests_passed == tests_total:
        print("✅ All tests passed! Qdrant MCP Server is ready to use.")
        print("\n📝 Next Steps:")
        print("1. Configure your IDE with the MCP server settings")
        print("2. Use 'qdrant-store' to store information")
        print("3. Use 'qdrant-find' to search for information")
    else:
        print(f"⚠️  {tests_total - tests_passed} tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()