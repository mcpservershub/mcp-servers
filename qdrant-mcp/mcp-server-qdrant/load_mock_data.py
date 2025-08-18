#!/usr/bin/env python3
"""
Mock Data Loader for Qdrant MCP Server Testing
This script loads various types of mock data into Qdrant for comprehensive testing
"""

import json
import time
import requests
import random
from typing import List, Dict, Any
from datetime import datetime, timedelta
import sys

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("⚠️  sentence-transformers not installed. Using random vectors instead.")
    print("   Install with: pip install sentence-transformers")

class MockDataLoader:
    def __init__(self, qdrant_url: str = "http://localhost:6333", 
                 collection_name: str = "test-collection",
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.api_base = f"{qdrant_url}"
        
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
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using model or random vector"""
        if self.encoder:
            return self.encoder.encode(text).tolist()
        else:
            # Generate deterministic pseudo-random vector based on text
            random.seed(hash(text) % 2**32)
            return [random.random() for _ in range(self.vector_size)]
    
    def ensure_collection(self) -> bool:
        """Ensure collection exists with proper configuration"""
        try:
            # Check if collection exists
            response = requests.get(f"{self.api_base}/collections/{self.collection_name}")
            
            if response.status_code == 404:
                # Create collection
                print(f"Creating collection '{self.collection_name}'...")
                payload = {
                    "vectors": {
                        "size": self.vector_size,
                        "distance": "Cosine"
                    }
                }
                response = requests.put(
                    f"{self.api_base}/collections/{self.collection_name}",
                    json=payload
                )
                if response.status_code == 200:
                    print(f"✅ Collection created")
                    return True
                else:
                    print(f"❌ Failed to create collection: {response.text}")
                    return False
            else:
                print(f"✅ Collection '{self.collection_name}' already exists")
                return True
        except Exception as e:
            print(f"❌ Error with collection: {e}")
            return False
    
    def load_code_snippets(self) -> int:
        """Load programming code snippets"""
        print("\n📝 Loading code snippets...")
        
        code_snippets = [
            {
                "language": "python",
                "title": "FastAPI endpoint for user authentication",
                "code": """@app.post("/auth/login")
async def login(credentials: UserCredentials):
    user = await get_user(credentials.username)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}""",
                "tags": ["api", "authentication", "fastapi", "python", "security"]
            },
            {
                "language": "javascript",
                "title": "React hook for fetching data with caching",
                "code": """const useDataFetch = (url) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const cache = useRef({});
  
  useEffect(() => {
    if (cache.current[url]) {
      setData(cache.current[url]);
      setLoading(false);
      return;
    }
    
    fetch(url)
      .then(res => res.json())
      .then(result => {
        cache.current[url] = result;
        setData(result);
        setLoading(false);
      });
  }, [url]);
  
  return { data, loading };
};""",
                "tags": ["react", "hooks", "javascript", "caching", "frontend"]
            },
            {
                "language": "python",
                "title": "Decorator for retry logic with exponential backoff",
                "code": """def retry_with_backoff(max_retries=3, base_delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
            return None
        return wrapper
    return decorator""",
                "tags": ["python", "decorator", "retry", "error-handling", "utilities"]
            },
            {
                "language": "sql",
                "title": "Query for finding duplicate records",
                "code": """WITH DuplicateRecords AS (
    SELECT 
        email,
        COUNT(*) as count,
        STRING_AGG(CAST(id AS VARCHAR), ', ') as duplicate_ids
    FROM users
    GROUP BY email
    HAVING COUNT(*) > 1
)
SELECT * FROM DuplicateRecords
ORDER BY count DESC;""",
                "tags": ["sql", "database", "query", "duplicates", "data-cleaning"]
            },
            {
                "language": "typescript",
                "title": "Generic type-safe event emitter class",
                "code": """class TypedEventEmitter<T extends Record<string, any[]>> {
  private events: Map<keyof T, Set<(...args: any[]) => void>> = new Map();
  
  on<K extends keyof T>(event: K, handler: (...args: T[K]) => void): void {
    if (!this.events.has(event)) {
      this.events.set(event, new Set());
    }
    this.events.get(event)!.add(handler);
  }
  
  emit<K extends keyof T>(event: K, ...args: T[K]): void {
    const handlers = this.events.get(event);
    if (handlers) {
      handlers.forEach(handler => handler(...args));
    }
  }
}""",
                "tags": ["typescript", "events", "generics", "design-pattern", "type-safety"]
            },
            {
                "language": "go",
                "title": "Concurrent worker pool implementation",
                "code": """func WorkerPool(jobs <-chan Job, results chan<- Result, workerCount int) {
    var wg sync.WaitGroup
    
    for i := 0; i < workerCount; i++ {
        wg.Add(1)
        go func(workerID int) {
            defer wg.Done()
            for job := range jobs {
                result := processJob(job)
                result.WorkerID = workerID
                results <- result
            }
        }(i)
    }
    
    wg.Wait()
    close(results)
}""",
                "tags": ["go", "concurrency", "worker-pool", "goroutines", "channels"]
            },
            {
                "language": "rust",
                "title": "Custom error type with thiserror",
                "code": """#[derive(Error, Debug)]
pub enum AppError {
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),
    
    #[error("Validation error: {message}")]
    Validation { message: String },
    
    #[error("Not found: {resource}")]
    NotFound { resource: String },
    
    #[error("Unauthorized")]
    Unauthorized,
}""",
                "tags": ["rust", "error-handling", "thiserror", "custom-types"]
            },
            {
                "language": "python",
                "title": "Async context manager for database connections",
                "code": """class AsyncDatabase:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.connection = None
    
    async def __aenter__(self):
        self.connection = await asyncpg.connect(self.connection_string)
        return self.connection
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            await self.connection.close()
        if exc_type:
            print(f"Exception occurred: {exc_val}")
        return False""",
                "tags": ["python", "async", "context-manager", "database", "asyncpg"]
            }
        ]
        
        points = []
        for i, snippet in enumerate(code_snippets):
            # Create searchable text
            searchable_text = f"{snippet['title']} {snippet['language']} {' '.join(snippet['tags'])} {snippet['code']}"
            
            # Generate embedding
            vector = self.generate_embedding(searchable_text)
            
            point = {
                "id": f"code_{i}",
                "vector": vector,
                "payload": {
                    "type": "code_snippet",
                    "title": snippet["title"],
                    "language": snippet["language"],
                    "code": snippet["code"],
                    "tags": snippet["tags"],
                    "timestamp": datetime.now().isoformat(),
                    "searchable_text": searchable_text
                }
            }
            points.append(point)
        
        return self._insert_points(points, "code snippets")
    
    def load_documentation(self) -> int:
        """Load technical documentation"""
        print("\n📚 Loading documentation...")
        
        docs = [
            {
                "title": "API Rate Limiting Best Practices",
                "content": """Rate limiting is essential for protecting APIs from abuse. Implement token bucket or sliding window algorithms. 
                Set appropriate limits based on user tiers. Use headers like X-RateLimit-Limit, X-RateLimit-Remaining, and X-RateLimit-Reset 
                to communicate limits to clients. Consider implementing exponential backoff for retry logic.""",
                "category": "api-design",
                "tags": ["api", "rate-limiting", "security", "best-practices"]
            },
            {
                "title": "Microservices Communication Patterns",
                "content": """Choose between synchronous (REST, gRPC) and asynchronous (message queues, event streaming) communication. 
                Implement circuit breakers for fault tolerance. Use service mesh for advanced traffic management. 
                Consider eventual consistency for distributed transactions. Implement proper service discovery mechanisms.""",
                "category": "architecture",
                "tags": ["microservices", "architecture", "communication", "distributed-systems"]
            },
            {
                "title": "Database Indexing Strategies",
                "content": """Create indexes on frequently queried columns. Use composite indexes for multi-column queries. 
                Avoid over-indexing as it slows down writes. Monitor index usage and remove unused ones. 
                Consider partial indexes for large tables. Use covering indexes to avoid table lookups.""",
                "category": "database",
                "tags": ["database", "performance", "indexing", "optimization"]
            },
            {
                "title": "Container Security Best Practices",
                "content": """Run containers as non-root users. Use minimal base images like Alpine or distroless. 
                Scan images for vulnerabilities regularly. Implement network policies for pod-to-pod communication. 
                Use secrets management tools instead of environment variables for sensitive data. Enable read-only root filesystems.""",
                "category": "security",
                "tags": ["docker", "kubernetes", "security", "containers", "devops"]
            },
            {
                "title": "CI/CD Pipeline Optimization",
                "content": """Parallelize independent build steps. Cache dependencies and Docker layers. 
                Run tests in parallel with proper test splitting. Use incremental builds when possible. 
                Implement early failing for quick feedback. Optimize Docker build context size.""",
                "category": "devops",
                "tags": ["ci-cd", "automation", "optimization", "devops", "pipeline"]
            },
            {
                "title": "GraphQL Schema Design",
                "content": """Design schemas with client needs in mind. Use proper naming conventions (camelCase for fields). 
                Implement pagination with cursor-based approach. Use DataLoader for N+1 query prevention. 
                Consider schema versioning strategies. Implement proper error handling with extensions.""",
                "category": "api-design",
                "tags": ["graphql", "api", "schema", "design", "best-practices"]
            },
            {
                "title": "Monitoring and Observability",
                "content": """Implement the three pillars: metrics, logs, and traces. Use structured logging with correlation IDs. 
                Set up meaningful alerts based on SLOs. Implement distributed tracing for microservices. 
                Use APM tools for performance monitoring. Create dashboards for key business metrics.""",
                "category": "operations",
                "tags": ["monitoring", "observability", "logging", "metrics", "tracing"]
            }
        ]
        
        points = []
        for i, doc in enumerate(docs):
            # Create searchable text
            searchable_text = f"{doc['title']} {doc['category']} {' '.join(doc['tags'])} {doc['content']}"
            
            # Generate embedding
            vector = self.generate_embedding(searchable_text)
            
            point = {
                "id": f"doc_{i}",
                "vector": vector,
                "payload": {
                    "type": "documentation",
                    "title": doc["title"],
                    "content": doc["content"],
                    "category": doc["category"],
                    "tags": doc["tags"],
                    "timestamp": datetime.now().isoformat(),
                    "searchable_text": searchable_text
                }
            }
            points.append(point)
        
        return self._insert_points(points, "documentation")
    
    def load_qa_pairs(self) -> int:
        """Load question-answer pairs"""
        print("\n❓ Loading Q&A pairs...")
        
        qa_pairs = [
            {
                "question": "How do I handle CORS errors in my web application?",
                "answer": """CORS errors occur when a web page tries to access resources from a different origin. To fix:
                1. Configure your server to include proper CORS headers (Access-Control-Allow-Origin)
                2. For development, use a proxy or configure your dev server
                3. For production, whitelist specific origins rather than using wildcard (*)
                4. Handle preflight requests for complex HTTP methods
                5. Include credentials if needed with Access-Control-Allow-Credentials""",
                "category": "web-development"
            },
            {
                "question": "What's the difference between JWT and session-based authentication?",
                "answer": """JWT (stateless): Token contains all user info, scalable for microservices, can't be revoked easily, larger request size.
                Session-based (stateful): Server stores session data, easier to revoke, smaller request size, requires session store for scaling.
                Choose JWT for distributed systems and mobile apps, sessions for traditional web apps with server-side rendering.""",
                "category": "authentication"
            },
            {
                "question": "How can I optimize Docker image size?",
                "answer": """1. Use multi-stage builds to exclude build dependencies
                2. Choose minimal base images (Alpine, distroless)
                3. Combine RUN commands to reduce layers
                4. Clean package manager cache in the same layer
                5. Use .dockerignore to exclude unnecessary files
                6. Order Dockerfile commands from least to most frequently changed""",
                "category": "docker"
            },
            {
                "question": "What are the best practices for handling secrets in Kubernetes?",
                "answer": """1. Use Kubernetes Secrets instead of ConfigMaps for sensitive data
                2. Enable encryption at rest for etcd
                3. Use external secret management tools (Vault, AWS Secrets Manager)
                4. Implement RBAC to limit secret access
                5. Rotate secrets regularly
                6. Never commit secrets to version control
                7. Use sealed secrets for GitOps workflows""",
                "category": "kubernetes"
            },
            {
                "question": "How do I debug memory leaks in Node.js applications?",
                "answer": """1. Use --inspect flag and Chrome DevTools for heap snapshots
                2. Monitor memory usage with process.memoryUsage()
                3. Look for common causes: event listeners, timers, closures, global variables
                4. Use tools like clinic.js or heapdump
                5. Implement proper cleanup in lifecycle methods
                6. Watch for circular references and large object retention""",
                "category": "nodejs"
            }
        ]
        
        points = []
        for i, qa in enumerate(qa_pairs):
            # Create searchable text
            searchable_text = f"{qa['question']} {qa['answer']} {qa['category']}"
            
            # Generate embedding
            vector = self.generate_embedding(searchable_text)
            
            point = {
                "id": f"qa_{i}",
                "vector": vector,
                "payload": {
                    "type": "qa_pair",
                    "question": qa["question"],
                    "answer": qa["answer"],
                    "category": qa["category"],
                    "timestamp": datetime.now().isoformat(),
                    "searchable_text": searchable_text
                }
            }
            points.append(point)
        
        return self._insert_points(points, "Q&A pairs")
    
    def load_error_solutions(self) -> int:
        """Load common error messages and their solutions"""
        print("\n🔧 Loading error solutions...")
        
        errors = [
            {
                "error": "Cannot read property 'undefined' of null",
                "language": "JavaScript",
                "solution": "Check for null/undefined before accessing properties. Use optional chaining (?.) or add null checks.",
                "example": "const value = obj?.property?.subproperty || defaultValue;"
            },
            {
                "error": "ModuleNotFoundError: No module named 'package_name'",
                "language": "Python",
                "solution": "Install the missing package using pip: pip install package_name. Check virtual environment activation.",
                "example": "pip install requests\n# or\npython -m pip install requests"
            },
            {
                "error": "ECONNREFUSED - Connection refused",
                "language": "Node.js",
                "solution": "Service is not running or wrong port. Check if the service is up and the port is correct.",
                "example": "Check: netstat -an | grep LISTEN\nVerify service is running: docker ps or systemctl status service"
            },
            {
                "error": "panic: runtime error: invalid memory address or nil pointer dereference",
                "language": "Go",
                "solution": "Check for nil pointers before dereferencing. Initialize structs and pointers properly.",
                "example": "if ptr != nil {\n    value = ptr.Field\n}"
            },
            {
                "error": "java.lang.NullPointerException",
                "language": "Java",
                "solution": "Check for null before using objects. Use Optional for better null handling.",
                "example": "Optional.ofNullable(object).ifPresent(obj -> obj.method());"
            }
        ]
        
        points = []
        for i, error in enumerate(errors):
            searchable_text = f"{error['error']} {error['language']} {error['solution']} {error['example']}"
            vector = self.generate_embedding(searchable_text)
            
            point = {
                "id": f"error_{i}",
                "vector": vector,
                "payload": {
                    "type": "error_solution",
                    "error": error["error"],
                    "language": error["language"],
                    "solution": error["solution"],
                    "example": error["example"],
                    "timestamp": datetime.now().isoformat(),
                    "searchable_text": searchable_text
                }
            }
            points.append(point)
        
        return self._insert_points(points, "error solutions")
    
    def load_project_notes(self) -> int:
        """Load project notes and decisions"""
        print("\n📋 Loading project notes...")
        
        notes = [
            {
                "project": "E-commerce Platform Migration",
                "date": "2024-03-15",
                "decision": "Migrate from monolith to microservices",
                "rationale": "Improve scalability, enable independent deployments, and allow team autonomy",
                "notes": "Start with extracting payment and inventory services. Use event sourcing for order management."
            },
            {
                "project": "API Gateway Implementation",
                "date": "2024-04-02",
                "decision": "Use Kong as API Gateway",
                "rationale": "Good plugin ecosystem, supports multiple protocols, has enterprise support",
                "notes": "Configure rate limiting, authentication, and request/response transformation plugins."
            },
            {
                "project": "Frontend Framework Selection",
                "date": "2024-05-10",
                "decision": "Adopt Next.js for new projects",
                "rationale": "SSR/SSG support, good developer experience, strong ecosystem, TypeScript first",
                "notes": "Migrate existing React apps gradually. Use App Router for new features."
            },
            {
                "project": "Database Sharding Strategy",
                "date": "2024-06-20",
                "decision": "Implement horizontal sharding by customer ID",
                "rationale": "Linear scalability, data isolation per customer, simplified compliance",
                "notes": "Use consistent hashing for shard selection. Implement cross-shard query aggregation service."
            }
        ]
        
        points = []
        for i, note in enumerate(notes):
            searchable_text = f"{note['project']} {note['decision']} {note['rationale']} {note['notes']}"
            vector = self.generate_embedding(searchable_text)
            
            point = {
                "id": f"note_{i}",
                "vector": vector,
                "payload": {
                    "type": "project_note",
                    "project": note["project"],
                    "date": note["date"],
                    "decision": note["decision"],
                    "rationale": note["rationale"],
                    "notes": note["notes"],
                    "timestamp": datetime.now().isoformat(),
                    "searchable_text": searchable_text
                }
            }
            points.append(point)
        
        return self._insert_points(points, "project notes")
    
    def _insert_points(self, points: List[Dict], data_type: str) -> int:
        """Insert points into Qdrant"""
        try:
            # Insert in batches
            batch_size = 50
            total_inserted = 0
            
            for i in range(0, len(points), batch_size):
                batch = points[i:i+batch_size]
                payload = {"points": batch}
                
                response = requests.put(
                    f"{self.api_base}/collections/{self.collection_name}/points",
                    json=payload
                )
                
                if response.status_code == 200:
                    total_inserted += len(batch)
                else:
                    print(f"⚠️  Failed to insert batch: {response.text}")
            
            print(f"✅ Inserted {total_inserted} {data_type}")
            return total_inserted
            
        except Exception as e:
            print(f"❌ Error inserting {data_type}: {e}")
            return 0
    
    def verify_data(self) -> Dict[str, Any]:
        """Verify loaded data and get statistics"""
        try:
            response = requests.get(f"{self.api_base}/collections/{self.collection_name}")
            if response.status_code == 200:
                info = response.json()["result"]
                
                # Get count by type
                type_counts = {}
                for data_type in ["code_snippet", "documentation", "qa_pair", "error_solution", "project_note"]:
                    count_response = requests.post(
                        f"{self.api_base}/collections/{self.collection_name}/points/count",
                        json={
                            "filter": {
                                "must": [{"key": "type", "match": {"value": data_type}}]
                            }
                        }
                    )
                    if count_response.status_code == 200:
                        type_counts[data_type] = count_response.json()["result"]["count"]
                
                return {
                    "total_points": info.get("points_count", 0),
                    "vector_size": info["config"]["params"]["vectors"]["size"],
                    "distance": info["config"]["params"]["vectors"]["distance"],
                    "status": info["status"],
                    "type_counts": type_counts
                }
            return {}
        except Exception as e:
            print(f"❌ Error verifying data: {e}")
            return {}
    
    def sample_searches(self):
        """Perform sample searches to demonstrate functionality"""
        print("\n🔍 Performing sample searches...")
        
        test_queries = [
            "How to implement authentication in FastAPI",
            "React hooks for data fetching",
            "Database optimization techniques",
            "Docker container security",
            "Handle null pointer exceptions"
        ]
        
        for query in test_queries:
            print(f"\n📝 Query: '{query}'")
            vector = self.generate_embedding(query)
            
            payload = {
                "vector": vector,
                "limit": 3,
                "with_payload": True
            }
            
            response = requests.post(
                f"{self.api_base}/collections/{self.collection_name}/points/search",
                json=payload
            )
            
            if response.status_code == 200:
                results = response.json()["result"]
                for i, result in enumerate(results, 1):
                    score = result.get("score", 0)
                    payload = result.get("payload", {})
                    data_type = payload.get("type", "unknown")
                    
                    if data_type == "code_snippet":
                        title = payload.get("title", "N/A")
                        print(f"  {i}. [{score:.3f}] Code: {title}")
                    elif data_type == "documentation":
                        title = payload.get("title", "N/A")
                        print(f"  {i}. [{score:.3f}] Doc: {title}")
                    elif data_type == "qa_pair":
                        question = payload.get("question", "N/A")[:50]
                        print(f"  {i}. [{score:.3f}] Q&A: {question}...")
                    elif data_type == "error_solution":
                        error = payload.get("error", "N/A")[:50]
                        print(f"  {i}. [{score:.3f}] Error: {error}...")
                    elif data_type == "project_note":
                        project = payload.get("project", "N/A")
                        print(f"  {i}. [{score:.3f}] Note: {project}")
            else:
                print(f"  ❌ Search failed: {response.text}")

def main():
    print("🚀 Qdrant Mock Data Loader")
    print("=" * 50)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Load mock data into Qdrant")
    parser.add_argument("--url", default="http://localhost:6333", help="Qdrant URL")
    parser.add_argument("--collection", default="test-collection", help="Collection name")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2", help="Embedding model")
    parser.add_argument("--skip-search", action="store_true", help="Skip sample searches")
    args = parser.parse_args()
    
    loader = MockDataLoader(args.url, args.collection, args.model)
    
    # Ensure collection exists
    if not loader.ensure_collection():
        print("❌ Failed to create/verify collection")
        sys.exit(1)
    
    # Load all data types
    total_loaded = 0
    total_loaded += loader.load_code_snippets()
    total_loaded += loader.load_documentation()
    total_loaded += loader.load_qa_pairs()
    total_loaded += loader.load_error_solutions()
    total_loaded += loader.load_project_notes()
    
    print(f"\n✅ Total points loaded: {total_loaded}")
    
    # Verify data
    print("\n📊 Verifying loaded data...")
    stats = loader.verify_data()
    if stats:
        print(f"  Total points in collection: {stats['total_points']}")
        print(f"  Vector size: {stats['vector_size']}")
        print(f"  Distance metric: {stats['distance']}")
        print(f"  Collection status: {stats['status']}")
        print("  Data type breakdown:")
        for data_type, count in stats.get('type_counts', {}).items():
            print(f"    - {data_type}: {count}")
    
    # Perform sample searches
    if not args.skip_search:
        loader.sample_searches()
    
    print("\n" + "=" * 50)
    print("✅ Mock data loading complete!")
    print("\nYou can now test the MCP server with commands like:")
    print("  - 'Store this information: ...'")
    print("  - 'Find information about: ...'")
    print(f"\nQdrant Dashboard: {args.url}/dashboard")

if __name__ == "__main__":
    main()