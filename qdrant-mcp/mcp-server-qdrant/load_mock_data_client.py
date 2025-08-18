#!/usr/bin/env python3
"""
Mock Data Loader using Qdrant Python Client
This script loads various types of mock data into Qdrant using the official Python client
"""

import time
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
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
        Range,
        SearchRequest,
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

class QdrantMockDataLoader:
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 6333,
                 collection_name: str = "test-collection",
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
                 api_key: Optional[str] = None):
        
        # Initialize Qdrant client
        self.client = QdrantClient(host=host, port=port, api_key=api_key)
        self.collection_name = collection_name
        
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
            collections = self.client.get_collections().collections
            collection_exists = any(c.name == self.collection_name for c in collections)
            
            if collection_exists and recreate:
                print(f"🗑️  Deleting existing collection '{self.collection_name}'...")
                self.client.delete_collection(self.collection_name)
                collection_exists = False
            
            if not collection_exists:
                print(f"📦 Creating collection '{self.collection_name}'...")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                print(f"✅ Collection created")
            else:
                print(f"✅ Collection '{self.collection_name}' already exists")
            
            # Get collection info
            info = self.client.get_collection(self.collection_name)
            print(f"📊 Collection info: {info.points_count} points, vector size: {info.config.params.vectors.size}")
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
                "title": "FastAPI WebSocket endpoint with authentication",
                "code": """@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, token: str = Query(...)):
    try:
        user = await verify_token(token)
        await manager.connect(websocket, client_id, user)
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await manager.broadcast(message, client_id)
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        await manager.broadcast({"type": "user_left", "client_id": client_id})""",
                "tags": ["fastapi", "websocket", "authentication", "python", "real-time"]
            },
            {
                "language": "typescript",
                "title": "React Query custom hook with optimistic updates",
                "code": """const useUpdateUser = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: updateUser,
    onMutate: async (newUser) => {
      await queryClient.cancelQueries({ queryKey: ['user', newUser.id] });
      const previousUser = queryClient.getQueryData(['user', newUser.id]);
      
      queryClient.setQueryData(['user', newUser.id], newUser);
      return { previousUser };
    },
    onError: (err, newUser, context) => {
      queryClient.setQueryData(['user', newUser.id], context.previousUser);
    },
    onSettled: (data, error, variables) => {
      queryClient.invalidateQueries({ queryKey: ['user', variables.id] });
    }
  });
};""",
                "tags": ["react", "react-query", "typescript", "optimistic-updates", "hooks"]
            },
            {
                "language": "go",
                "title": "Middleware for request rate limiting with Redis",
                "code": """func RateLimitMiddleware(rdb *redis.Client, limit int) gin.HandlerFunc {
    return func(c *gin.Context) {
        ctx := context.Background()
        key := fmt.Sprintf("rate_limit:%s", c.ClientIP())
        
        pipe := rdb.Pipeline()
        incr := pipe.Incr(ctx, key)
        pipe.Expire(ctx, key, time.Minute)
        _, err := pipe.Exec(ctx)
        
        if err != nil {
            c.AbortWithStatus(http.StatusInternalServerError)
            return
        }
        
        if incr.Val() > int64(limit) {
            c.AbortWithStatus(http.StatusTooManyRequests)
            return
        }
        
        c.Next()
    }
}""",
                "tags": ["go", "middleware", "rate-limiting", "redis", "gin"]
            },
            {
                "language": "rust",
                "title": "Async stream processing with tokio",
                "code": """use tokio_stream::{Stream, StreamExt};

async fn process_stream<S>(mut stream: S) -> Result<Vec<ProcessedItem>, Error>
where
    S: Stream<Item = RawItem> + Unpin,
{
    let mut results = Vec::new();
    let semaphore = Arc::new(Semaphore::new(10)); // Limit concurrent processing
    
    while let Some(item) = stream.next().await {
        let permit = semaphore.clone().acquire_owned().await?;
        
        let handle = tokio::spawn(async move {
            let _permit = permit; // Hold permit until processing completes
            process_item(item).await
        });
        
        results.push(handle);
    }
    
    futures::future::try_join_all(results).await
}""",
                "tags": ["rust", "async", "tokio", "stream-processing", "concurrency"]
            },
            {
                "language": "python",
                "title": "SQLAlchemy async session with context manager",
                "code": """from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

class DatabaseManager:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    @asynccontextmanager
    async def session(self):
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self):
        await self.engine.dispose()""",
                "tags": ["python", "sqlalchemy", "async", "database", "context-manager"]
            },
            {
                "language": "javascript",
                "title": "WebRTC peer connection setup with error handling",
                "code": """class PeerConnection {
  constructor(configuration) {
    this.pc = new RTCPeerConnection(configuration);
    this.setupEventHandlers();
  }
  
  setupEventHandlers() {
    this.pc.onicecandidate = (event) => {
      if (event.candidate) {
        this.sendSignal({ type: 'ice-candidate', candidate: event.candidate });
      }
    };
    
    this.pc.onconnectionstatechange = () => {
      console.log('Connection state:', this.pc.connectionState);
      if (this.pc.connectionState === 'failed') {
        this.handleConnectionFailure();
      }
    };
  }
  
  async createOffer() {
    try {
      const offer = await this.pc.createOffer();
      await this.pc.setLocalDescription(offer);
      return offer;
    } catch (error) {
      console.error('Failed to create offer:', error);
      throw error;
    }
  }
}""",
                "tags": ["javascript", "webrtc", "peer-connection", "real-time", "networking"]
            },
            {
                "language": "python",
                "title": "Celery task with retry and exponential backoff",
                "code": """from celery import Task
from celery.exceptions import Retry
import requests

class RetryableTask(Task):
    autoretry_for = (requests.RequestException,)
    retry_kwargs = {'max_retries': 5}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True

@app.task(base=RetryableTask, bind=True)
def fetch_external_data(self, url: str, params: dict):
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        print(f"Request failed: {exc}, retrying...")
        raise self.retry(exc=exc)""",
                "tags": ["python", "celery", "async-tasks", "retry", "error-handling"]
            },
            {
                "language": "sql",
                "title": "Window function for running totals and rankings",
                "code": """WITH sales_analysis AS (
    SELECT 
        date,
        product_id,
        quantity,
        price,
        quantity * price as revenue,
        SUM(quantity * price) OVER (
            PARTITION BY product_id 
            ORDER BY date 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) as running_total,
        RANK() OVER (
            PARTITION BY DATE_TRUNC('month', date)
            ORDER BY quantity * price DESC
        ) as monthly_rank
    FROM sales
    WHERE date >= DATE_TRUNC('year', CURRENT_DATE)
)
SELECT * FROM sales_analysis
WHERE monthly_rank <= 10
ORDER BY date, monthly_rank;""",
                "tags": ["sql", "window-functions", "analytics", "postgresql", "reporting"]
            }
        ]
        
        points = []
        for i, snippet in enumerate(code_snippets):
            # Create searchable text
            searchable_text = f"{snippet['title']} {snippet['language']} {' '.join(snippet['tags'])} {snippet['code']}"
            
            # Generate embedding
            vector = self.generate_embedding(searchable_text)
            
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "type": "code_snippet",
                    "title": snippet["title"],
                    "language": snippet["language"],
                    "code": snippet["code"],
                    "tags": snippet["tags"],
                    "timestamp": datetime.now().isoformat(),
                    "searchable_text": searchable_text
                }
            )
            points.append(point)
        
        return self._upsert_points(points, "code snippets")
    
    def load_documentation(self) -> int:
        """Load technical documentation"""
        print("\n📚 Loading documentation...")
        
        docs = [
            {
                "title": "Zero-Downtime Deployment Strategies",
                "content": """Implement blue-green deployments for instant rollback capability. Use rolling updates with health checks in Kubernetes. 
                Configure proper readiness and liveness probes. Implement database migration strategies with backward compatibility. 
                Use feature flags for gradual rollout. Monitor key metrics during deployment. Have automated rollback triggers based on error rates.""",
                "category": "devops",
                "tags": ["deployment", "zero-downtime", "kubernetes", "blue-green", "devops"]
            },
            {
                "title": "Event-Driven Architecture Patterns",
                "content": """Use event sourcing for audit trails and time travel debugging. Implement CQRS for read/write optimization. 
                Choose between choreography and orchestration patterns. Use schema registry for event versioning. 
                Implement idempotent consumers. Handle out-of-order events with event timestamps. Use dead letter queues for failed messages.""",
                "category": "architecture",
                "tags": ["event-driven", "microservices", "event-sourcing", "CQRS", "patterns"]
            },
            {
                "title": "API Versioning Strategies",
                "content": """Use URL path versioning for clear separation (/v1/, /v2/). Implement header-based versioning for flexibility. 
                Support multiple versions simultaneously with deprecation notices. Use semantic versioning for clear communication. 
                Implement version negotiation. Maintain backward compatibility. Document breaking changes clearly.""",
                "category": "api-design",
                "tags": ["api", "versioning", "rest", "backward-compatibility", "design"]
            },
            {
                "title": "Distributed Tracing Implementation",
                "content": """Implement OpenTelemetry for vendor-neutral instrumentation. Use correlation IDs across services. 
                Set up trace sampling to manage costs. Configure span attributes for debugging. Integrate with APM tools. 
                Create custom spans for business operations. Use baggage for cross-service context propagation.""",
                "category": "observability",
                "tags": ["tracing", "opentelemetry", "observability", "monitoring", "debugging"]
            },
            {
                "title": "Database Connection Pooling Best Practices",
                "content": """Configure pool size based on database limits and application needs. Set appropriate timeout values. 
                Implement connection validation queries. Use connection pool monitoring. Handle connection leaks with proper cleanup. 
                Configure idle connection timeout. Implement circuit breakers for database failures.""",
                "category": "database",
                "tags": ["database", "connection-pooling", "performance", "optimization", "best-practices"]
            },
            {
                "title": "Secrets Management in Cloud Native Applications",
                "content": """Use external secret stores (Vault, AWS Secrets Manager). Implement secret rotation policies. 
                Encrypt secrets at rest and in transit. Use least privilege access principles. Audit secret access. 
                Implement break-glass procedures. Never store secrets in code or version control.""",
                "category": "security",
                "tags": ["security", "secrets-management", "cloud-native", "vault", "best-practices"]
            },
            {
                "title": "Load Testing and Performance Benchmarking",
                "content": """Start with baseline measurements. Use realistic data volumes and patterns. Test with production-like infrastructure. 
                Implement gradual load increase. Monitor all system components during tests. Document performance requirements. 
                Use tools like K6, JMeter, or Gatling. Test API endpoints, database queries, and frontend performance separately.""",
                "category": "testing",
                "tags": ["performance", "load-testing", "benchmarking", "testing", "optimization"]
            },
            {
                "title": "Caching Strategies and Patterns",
                "content": """Implement multi-level caching (browser, CDN, application, database). Use cache-aside pattern for flexibility. 
                Implement write-through for consistency. Set appropriate TTL values. Handle cache invalidation carefully. 
                Monitor cache hit rates. Use cache warming for predictable loads. Implement cache stampede prevention.""",
                "category": "performance",
                "tags": ["caching", "performance", "redis", "patterns", "optimization"]
            }
        ]
        
        points = []
        for i, doc in enumerate(docs):
            searchable_text = f"{doc['title']} {doc['category']} {' '.join(doc['tags'])} {doc['content']}"
            vector = self.generate_embedding(searchable_text)
            
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "type": "documentation",
                    "title": doc["title"],
                    "content": doc["content"],
                    "category": doc["category"],
                    "tags": doc["tags"],
                    "timestamp": datetime.now().isoformat(),
                    "searchable_text": searchable_text
                }
            )
            points.append(point)
        
        return self._upsert_points(points, "documentation")
    
    def load_troubleshooting_guides(self) -> int:
        """Load troubleshooting guides for common issues"""
        print("\n🔧 Loading troubleshooting guides...")
        
        guides = [
            {
                "issue": "High memory usage in Node.js application",
                "symptoms": ["Process consuming excessive RAM", "Frequent garbage collection", "Application crashes with heap errors"],
                "diagnosis": "Use --inspect flag with Chrome DevTools. Take heap snapshots. Check for memory leaks in event listeners, timers, and closures.",
                "solution": """1. Remove unused event listeners
2. Clear timers and intervals properly
3. Avoid storing large objects in closure scope
4. Use streams for large data processing
5. Implement proper cleanup in component lifecycle
6. Set --max-old-space-size appropriately""",
                "tags": ["nodejs", "memory", "performance", "debugging"]
            },
            {
                "issue": "Kubernetes pod constantly restarting",
                "symptoms": ["CrashLoopBackOff status", "High restart count", "Pod never reaches ready state"],
                "diagnosis": "Check pod logs with kubectl logs. Review pod events. Check resource limits. Verify health check configuration.",
                "solution": """1. Review application logs for startup errors
2. Increase initialDelaySeconds for health checks
3. Check resource limits (memory/CPU)
4. Verify environment variables and configs
5. Check for missing dependencies or services
6. Review security context and permissions""",
                "tags": ["kubernetes", "containers", "troubleshooting", "devops"]
            },
            {
                "issue": "Database query performance degradation",
                "symptoms": ["Slow response times", "High CPU usage on database", "Query timeouts"],
                "diagnosis": "Use EXPLAIN ANALYZE for query plans. Check for missing indexes. Monitor table statistics. Review connection pool usage.",
                "solution": """1. Add appropriate indexes on filtered/joined columns
2. Update table statistics (ANALYZE command)
3. Rewrite queries to use indexes effectively
4. Implement query result caching
5. Consider partitioning large tables
6. Optimize connection pool settings""",
                "tags": ["database", "performance", "sql", "optimization"]
            },
            {
                "issue": "CORS errors in web application",
                "symptoms": ["Blocked by CORS policy errors", "Preflight request failures", "Missing headers in response"],
                "diagnosis": "Check browser console for specific CORS errors. Verify server CORS configuration. Check preflight response headers.",
                "solution": """1. Configure Access-Control-Allow-Origin correctly
2. Handle OPTIONS preflight requests
3. Set Access-Control-Allow-Methods for allowed HTTP methods
4. Include Access-Control-Allow-Headers for custom headers
5. Set Access-Control-Allow-Credentials for cookies
6. Use proxy in development environment""",
                "tags": ["web", "cors", "security", "api", "frontend"]
            },
            {
                "issue": "Docker build taking too long",
                "symptoms": ["Build times over 10 minutes", "Repeated dependency downloads", "Large image sizes"],
                "diagnosis": "Analyze build layers. Check Docker cache usage. Review Dockerfile order. Monitor network usage during build.",
                "solution": """1. Order Dockerfile commands from least to most frequently changed
2. Use multi-stage builds to reduce final image size
3. Leverage build cache with proper layer ordering
4. Use .dockerignore to exclude unnecessary files
5. Cache package manager downloads
6. Use smaller base images (Alpine, distroless)""",
                "tags": ["docker", "performance", "devops", "optimization"]
            }
        ]
        
        points = []
        for i, guide in enumerate(guides):
            searchable_text = f"{guide['issue']} {' '.join(guide['symptoms'])} {guide['diagnosis']} {guide['solution']} {' '.join(guide['tags'])}"
            vector = self.generate_embedding(searchable_text)
            
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "type": "troubleshooting_guide",
                    "issue": guide["issue"],
                    "symptoms": guide["symptoms"],
                    "diagnosis": guide["diagnosis"],
                    "solution": guide["solution"],
                    "tags": guide["tags"],
                    "timestamp": datetime.now().isoformat(),
                    "searchable_text": searchable_text
                }
            )
            points.append(point)
        
        return self._upsert_points(points, "troubleshooting guides")
    
    def load_architecture_decisions(self) -> int:
        """Load architecture decision records (ADRs)"""
        print("\n🏗️  Loading architecture decisions...")
        
        adrs = [
            {
                "title": "ADR-001: Adopt Microservices Architecture",
                "date": "2024-01-15",
                "status": "Accepted",
                "context": "Monolithic application becoming difficult to scale and deploy independently",
                "decision": "Migrate to microservices architecture with service mesh",
                "consequences": "Increased complexity, need for distributed tracing, improved scalability and team autonomy",
                "tags": ["architecture", "microservices", "scaling"]
            },
            {
                "title": "ADR-002: Use Event Streaming for Inter-Service Communication",
                "date": "2024-02-20",
                "status": "Accepted",
                "context": "Need for reliable, scalable communication between microservices",
                "decision": "Implement Apache Kafka for event streaming with Avro schemas",
                "consequences": "Eventually consistent system, need for schema registry, improved decoupling",
                "tags": ["kafka", "event-streaming", "microservices"]
            },
            {
                "title": "ADR-003: Implement GitOps for Deployments",
                "date": "2024-03-10",
                "status": "Accepted",
                "context": "Manual deployments causing errors and lack of audit trail",
                "decision": "Use ArgoCD for GitOps-based continuous deployment",
                "consequences": "Git as single source of truth, improved audit trail, need for proper git workflow",
                "tags": ["gitops", "argocd", "deployment", "kubernetes"]
            },
            {
                "title": "ADR-004: Adopt GraphQL for Public API",
                "date": "2024-04-05",
                "status": "Proposed",
                "context": "Multiple REST endpoints causing overfetching and underfetching issues",
                "decision": "Implement GraphQL gateway with federation for microservices",
                "consequences": "Better client flexibility, increased backend complexity, need for query optimization",
                "tags": ["graphql", "api", "federation"]
            }
        ]
        
        points = []
        for i, adr in enumerate(adrs):
            searchable_text = f"{adr['title']} {adr['context']} {adr['decision']} {adr['consequences']} {' '.join(adr['tags'])}"
            vector = self.generate_embedding(searchable_text)
            
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "type": "architecture_decision",
                    "title": adr["title"],
                    "date": adr["date"],
                    "status": adr["status"],
                    "context": adr["context"],
                    "decision": adr["decision"],
                    "consequences": adr["consequences"],
                    "tags": adr["tags"],
                    "timestamp": datetime.now().isoformat(),
                    "searchable_text": searchable_text
                }
            )
            points.append(point)
        
        return self._upsert_points(points, "architecture decisions")
    
    def _upsert_points(self, points: List[PointStruct], data_type: str) -> int:
        """Upsert points into Qdrant using the client"""
        try:
            # Upsert in batches
            batch_size = 100
            total_upserted = 0
            
            for i in range(0, len(points), batch_size):
                batch = points[i:i+batch_size]
                
                result = self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch,
                    wait=True
                )
                
                if result.status == UpdateStatus.COMPLETED:
                    total_upserted += len(batch)
                else:
                    print(f"⚠️  Failed to upsert batch: {result}")
            
            print(f"✅ Upserted {total_upserted} {data_type}")
            return total_upserted
            
        except Exception as e:
            print(f"❌ Error upserting {data_type}: {e}")
            return 0
    
    def verify_and_search(self):
        """Verify data and perform sample searches"""
        try:
            # Get collection info
            collection_info = self.client.get_collection(self.collection_name)
            print(f"\n📊 Collection Statistics:")
            print(f"  Total points: {collection_info.points_count}")
            print(f"  Vector size: {collection_info.config.params.vectors.size}")
            print(f"  Distance metric: {collection_info.config.params.vectors.distance}")
            
            # Count by type
            print("\n📈 Data type breakdown:")
            for data_type in ["code_snippet", "documentation", "troubleshooting_guide", "architecture_decision"]:
                result = self.client.count(
                    collection_name=self.collection_name,
                    count_filter=Filter(
                        must=[FieldCondition(key="type", match=Match(value=data_type))]
                    )
                )
                print(f"  - {data_type}: {result.count}")
            
            # Perform sample searches
            print("\n🔍 Sample Searches:")
            test_queries = [
                "How to implement WebSocket authentication",
                "Kubernetes pod troubleshooting",
                "Database performance optimization",
                "Event-driven architecture patterns",
                "Docker build optimization"
            ]
            
            for query in test_queries:
                print(f"\n🔎 Query: '{query}'")
                vector = self.generate_embedding(query)
                
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=vector,
                    limit=3,
                    with_payload=True
                )
                
                for i, result in enumerate(results, 1):
                    payload = result.payload
                    data_type = payload.get("type", "unknown")
                    
                    if data_type == "code_snippet":
                        title = payload.get("title", "N/A")
                        language = payload.get("language", "N/A")
                        print(f"  {i}. [{result.score:.3f}] Code ({language}): {title}")
                    elif data_type == "documentation":
                        title = payload.get("title", "N/A")
                        print(f"  {i}. [{result.score:.3f}] Doc: {title}")
                    elif data_type == "troubleshooting_guide":
                        issue = payload.get("issue", "N/A")
                        print(f"  {i}. [{result.score:.3f}] Guide: {issue}")
                    elif data_type == "architecture_decision":
                        title = payload.get("title", "N/A")
                        print(f"  {i}. [{result.score:.3f}] ADR: {title}")
                        
        except Exception as e:
            print(f"❌ Error during verification: {e}")

def main():
    print("🚀 Qdrant Mock Data Loader (Using Python Client)")
    print("=" * 50)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Load mock data into Qdrant using Python client")
    parser.add_argument("--host", default="localhost", help="Qdrant host")
    parser.add_argument("--port", type=int, default=6333, help="Qdrant port")
    parser.add_argument("--collection", default="test-collection", help="Collection name")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2", help="Embedding model")
    parser.add_argument("--recreate", action="store_true", help="Recreate collection (delete existing)")
    parser.add_argument("--skip-search", action="store_true", help="Skip sample searches")
    args = parser.parse_args()
    
    # Check Qdrant connection
    try:
        client = QdrantClient(host=args.host, port=args.port)
        client.get_collections()
        print(f"✅ Connected to Qdrant at {args.host}:{args.port}")
    except Exception as e:
        print(f"❌ Cannot connect to Qdrant: {e}")
        print("   Please ensure Qdrant is running: docker-compose up -d")
        sys.exit(1)
    
    # Initialize loader
    loader = QdrantMockDataLoader(
        host=args.host,
        port=args.port,
        collection_name=args.collection,
        embedding_model=args.model
    )
    
    # Ensure collection exists
    if not loader.ensure_collection(recreate=args.recreate):
        print("❌ Failed to create/verify collection")
        sys.exit(1)
    
    # Load all data types
    total_loaded = 0
    total_loaded += loader.load_code_snippets()
    total_loaded += loader.load_documentation()
    total_loaded += loader.load_troubleshooting_guides()
    total_loaded += loader.load_architecture_decisions()
    
    print(f"\n✅ Total points loaded: {total_loaded}")
    
    # Verify and search
    if not args.skip_search:
        loader.verify_and_search()
    
    print("\n" + "=" * 50)
    print("✅ Mock data loading complete!")
    print("\nYou can now test the MCP server with commands like:")
    print("  - 'Store this information: ...'")
    print("  - 'Find information about: ...'")
    print(f"\n📊 Qdrant Dashboard: http://{args.host}:{args.port}/dashboard")
    print(f"📡 Collection: {args.collection}")

if __name__ == "__main__":
    main()