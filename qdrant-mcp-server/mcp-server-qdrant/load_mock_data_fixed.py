#!/usr/bin/env python3
"""
Fixed Mock Data Loader for Qdrant MCP Server
This version uses the correct vector field name that matches the MCP server's expectations
"""

import time
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys
import uuid

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance, 
        VectorParams, 
        PointStruct,
        Filter,
        FieldCondition,
        Match,
        UpdateStatus
    )
    QDRANT_CLIENT_AVAILABLE = True
except ImportError:
    QDRANT_CLIENT_AVAILABLE = False
    print("❌ qdrant-client not installed.")
    print("   Install with: pip install qdrant-client")
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("⚠️  sentence-transformers not installed. Using random vectors instead.")
    print("   Install with: pip install sentence-transformers")

class QdrantMCPDataLoader:
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 6333,
                 collection_name: str = "test-collection",
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
                 api_key: Optional[str] = None):
        
        # Initialize Qdrant client
        self.client = QdrantClient(host=host, port=port, api_key=api_key)
        self.collection_name = collection_name
        
        # IMPORTANT: Match the MCP server's vector field naming convention
        # For fastembed provider, it uses "fast-{model_name}"
        model_short_name = embedding_model.split("/")[-1].lower()
        self.vector_field_name = f"fast-{model_short_name}"
        
        # Initialize embedding model if available
        self.encoder = None
        if EMBEDDINGS_AVAILABLE:
            try:
                print(f"Loading embedding model: {embedding_model}")
                self.encoder = SentenceTransformer(embedding_model)
                self.vector_size = self.encoder.get_sentence_embedding_dimension()
                print(f"✅ Model loaded. Vector size: {self.vector_size}")
            except Exception as e:
                print(f"⚠️  Failed to load model: {e}")
                self.vector_size = 384
        else:
            self.vector_size = 384
        
        print(f"📡 Connected to Qdrant at {host}:{port}")
        print(f"🔧 Using vector field name: {self.vector_field_name}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using model or random vector"""
        if self.encoder:
            return self.encoder.encode(text).tolist()
        else:
            # Generate deterministic pseudo-random vector based on text
            random.seed(hash(text) % 2**32)
            return [random.random() for _ in range(self.vector_size)]
    
    def ensure_collection(self, recreate: bool = False) -> bool:
        """Ensure collection exists with proper configuration"""
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_exists = any(c.name == self.collection_name for c in collections)
            
            if collection_exists and recreate:
                print(f"🗑️  Deleting existing collection '{self.collection_name}'...")
                self.client.delete_collection(self.collection_name)
                collection_exists = False
            
            if not collection_exists:
                print(f"📦 Creating collection '{self.collection_name}' with vector field '{self.vector_field_name}'...")
                # Create collection with NAMED vector field to match MCP server
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config={
                        self.vector_field_name: VectorParams(
                            size=self.vector_size,
                            distance=Distance.COSINE
                        )
                    }
                )
                print(f"✅ Collection created with named vector field")
            else:
                # Verify the existing collection has the correct vector field
                info = self.client.get_collection(self.collection_name)
                if hasattr(info.config.params.vectors, 'size'):
                    # Old unnamed vector config - need to recreate
                    print(f"⚠️  Collection has unnamed vector field. Recreating...")
                    self.client.delete_collection(self.collection_name)
                    self.client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config={
                            self.vector_field_name: VectorParams(
                                size=self.vector_size,
                                distance=Distance.COSINE
                            )
                        }
                    )
                    print(f"✅ Collection recreated with named vector field")
                else:
                    print(f"✅ Collection '{self.collection_name}' exists with correct configuration")
            
            # Get collection info
            info = self.client.get_collection(self.collection_name)
            print(f"📊 Collection info: {info.points_count} points")
            return True
            
        except Exception as e:
            print(f"❌ Error with collection: {e}")
            return False
    
    def load_all_data(self) -> int:
        """Load all types of mock data"""
        total = 0
        
        # Load code snippets
        code_snippets = [
            {
                "title": "FastAPI WebSocket with authentication",
                "language": "python",
                "code": """@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, token: str = Query(...)):
    user = await verify_token(token)
    await manager.connect(websocket, client_id, user)
    while True:
        data = await websocket.receive_text()
        await manager.broadcast(json.loads(data), client_id)""",
                "tags": ["fastapi", "websocket", "authentication", "python"]
            },
            {
                "title": "React Query custom hook",
                "language": "typescript",
                "code": """const useUpdateUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateUser,
    onMutate: async (newUser) => {
      await queryClient.cancelQueries(['user', newUser.id]);
      const prev = queryClient.getQueryData(['user', newUser.id]);
      queryClient.setQueryData(['user', newUser.id], newUser);
      return { prev };
    }
  });
};""",
                "tags": ["react", "typescript", "react-query", "hooks"]
            },
            {
                "title": "Kubernetes pod debugging guide",
                "language": "yaml",
                "code": """apiVersion: v1
kind: Pod
metadata:
  name: debug-pod
spec:
  containers:
  - name: debug
    image: busybox
    command: ['sh', '-c', 'sleep 3600']
    resources:
      limits:
        memory: "128Mi"
        cpu: "500m"""",
                "tags": ["kubernetes", "debugging", "yaml", "devops"]
            },
            {
                "title": "Database connection pooling in Go",
                "language": "go",
                "code": """db, err := sql.Open("postgres", connStr)
if err != nil {
    log.Fatal(err)
}
db.SetMaxOpenConns(25)
db.SetMaxIdleConns(5)
db.SetConnMaxLifetime(5 * time.Minute)
defer db.Close()""",
                "tags": ["go", "database", "postgresql", "connection-pooling"]
            }
        ]
        
        # Load documentation
        docs = [
            {
                "title": "Docker Multi-Stage Build Best Practices",
                "content": "Use multi-stage builds to reduce image size. Copy only necessary files. Order layers from least to most frequently changed. Clean package caches in the same RUN command.",
                "category": "devops",
                "tags": ["docker", "optimization", "best-practices"]
            },
            {
                "title": "API Rate Limiting Strategies",
                "content": "Implement token bucket or sliding window algorithms. Use Redis for distributed rate limiting. Return proper headers: X-RateLimit-Limit, X-RateLimit-Remaining.",
                "category": "api-design",
                "tags": ["api", "rate-limiting", "security"]
            },
            {
                "title": "Microservices Communication Patterns",
                "content": "Choose between synchronous (REST, gRPC) and asynchronous (message queues). Implement circuit breakers. Use service mesh for traffic management.",
                "category": "architecture",
                "tags": ["microservices", "architecture", "patterns"]
            }
        ]
        
        # Load troubleshooting guides
        troubleshooting = [
            {
                "issue": "Kubernetes Pod CrashLoopBackOff",
                "solution": "Check logs with kubectl logs. Verify resource limits. Check liveness/readiness probes. Ensure all environment variables are set.",
                "tags": ["kubernetes", "debugging", "containers"]
            },
            {
                "issue": "High memory usage in Node.js",
                "solution": "Use --inspect flag for heap snapshots. Check for memory leaks in event listeners. Clear timers properly. Avoid global variables.",
                "tags": ["nodejs", "performance", "memory"]
            }
        ]
        
        points = []
        
        # Process code snippets
        for snippet in code_snippets:
            text = f"{snippet['title']} {snippet['language']} {' '.join(snippet['tags'])} {snippet['code']}"
            vector = self.generate_embedding(text)
            
            # IMPORTANT: Use the named vector field
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector={self.vector_field_name: vector},  # Named vector field
                payload={
                    "document": text,  # MCP server expects "document" field
                    "metadata": {      # MCP server expects "metadata" field
                        "type": "code_snippet",
                        "title": snippet["title"],
                        "language": snippet["language"],
                        "tags": snippet["tags"]
                    }
                }
            )
            points.append(point)
        
        # Process documentation
        for doc in docs:
            text = f"{doc['title']} {doc['content']} {' '.join(doc['tags'])}"
            vector = self.generate_embedding(text)
            
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector={self.vector_field_name: vector},
                payload={
                    "document": text,
                    "metadata": {
                        "type": "documentation",
                        "title": doc["title"],
                        "category": doc["category"],
                        "tags": doc["tags"]
                    }
                }
            )
            points.append(point)
        
        # Process troubleshooting guides
        for guide in troubleshooting:
            text = f"{guide['issue']} {guide['solution']} {' '.join(guide['tags'])}"
            vector = self.generate_embedding(text)
            
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector={self.vector_field_name: vector},
                payload={
                    "document": text,
                    "metadata": {
                        "type": "troubleshooting",
                        "issue": guide["issue"],
                        "tags": guide["tags"]
                    }
                }
            )
            points.append(point)
        
        # Upsert all points
        try:
            result = self.client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True
            )
            
            if result.status == UpdateStatus.COMPLETED:
                total = len(points)
                print(f"✅ Loaded {total} items into collection")
            else:
                print(f"❌ Failed to load data: {result}")
        except Exception as e:
            print(f"❌ Error loading data: {e}")
        
        return total
    
    def verify_search(self):
        """Verify data can be searched with named vectors"""
        print("\n🔍 Testing search with named vectors...")
        
        test_queries = [
            "FastAPI WebSocket authentication",
            "Kubernetes debugging",
            "Docker optimization"
        ]
        
        for query in test_queries:
            print(f"\n📝 Query: '{query}'")
            vector = self.generate_embedding(query)
            
            try:
                # Search using the named vector field
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=(self.vector_field_name, vector),  # Named vector search
                    limit=3,
                    with_payload=True
                )
                
                for i, result in enumerate(results, 1):
                    metadata = result.payload.get("metadata", {})
                    title = metadata.get("title", metadata.get("issue", "Unknown"))
                    score = result.score
                    print(f"   {i}. [{score:.3f}] {title}")
                    
            except Exception as e:
                print(f"   ❌ Search error: {e}")

def main():
    print("🚀 Fixed Qdrant Mock Data Loader for MCP Server")
    print("=" * 50)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Load mock data with correct vector field names")
    parser.add_argument("--collection", default="test_collection", help="Collection name (default: test_collection)")
    parser.add_argument("--host", default="localhost", help="Qdrant host")
    parser.add_argument("--port", type=int, default=6333, help="Qdrant port")
    args = parser.parse_args()
    
    print(f"📝 Using collection name: {args.collection}")
    
    # Check Qdrant connection
    try:
        client = QdrantClient(host=args.host, port=args.port)
        client.get_collections()
        print("✅ Connected to Qdrant")
    except Exception as e:
        print(f"❌ Cannot connect to Qdrant: {e}")
        print("   Please ensure Qdrant is running: docker-compose up -d")
        sys.exit(1)
    
    # Initialize loader with specified collection name
    loader = QdrantMCPDataLoader(
        host=args.host,
        port=args.port,
        collection_name=args.collection
    )
    
    # Ensure collection with correct configuration
    if not loader.ensure_collection(recreate=True):  # Force recreate to fix vector field
        print("❌ Failed to create collection")
        sys.exit(1)
    
    # Load mock data
    total = loader.load_all_data()
    
    if total > 0:
        # Verify with search
        loader.verify_search()
        
        print("\n" + "=" * 50)
        print("✅ Mock data loaded successfully!")
        print(f"📊 Total items: {total}")
        print(f"🔧 Vector field name: {loader.vector_field_name}")
        print("\n📝 Now you can test with MCP Inspector:")
        print("   npx @modelcontextprotocol/inspector uvx mcp-server-qdrant")
        print("\n💡 Example queries to try:")
        print("   - 'FastAPI authentication'")
        print("   - 'Kubernetes troubleshooting'")
        print("   - 'Docker best practices'")
    else:
        print("❌ No data was loaded")
        sys.exit(1)

if __name__ == "__main__":
    main()