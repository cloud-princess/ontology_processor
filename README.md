# Ontology Question Answering Engine

A production-ready, high-performance ontology reasoning system built with Python's asyncio framework. This system provides intelligent question answering capabilities over knowledge graphs with enterprise-grade observability, resilience patterns, and extensible architecture.

## 🏗️ System Architecture

The system follows a clean, layered architecture with clear separation of concerns:

```
├── src/
│   ├── domain/               # Domain models and business logic
│   │   ├── models.py         # Core entities (Entity, Relationship, Question)
│   │   └── exceptions.py     # Domain-specific exceptions
│   ├── application/          # Application services and orchestration
│   │   ├── services/         # Business logic services
│   │   └── orchestrator.py   # Main application coordinator
│   ├── infrastructure/       # External integrations and adapters
│   │   ├── storage/          # Data persistence abstractions
│   │   ├── caching/          # Caching layer implementations
│   │   ├── ingestion/        # Data ingestion adapters
│   │   └── resilience/       # Circuit breakers, retry logic
│   ├── observability/        # Metrics, logging, and monitoring
│   │   ├── metrics.py        # Metrics collection abstractions
│   │   └── instrumentation.py # Decorator-based instrumentation
│   └── config/               # Configuration management
       └── settings.py        # Environment-based configuration
```

## 🚀 Key Features

### 1. Intelligent Question Answering
- **Multi-type Query Support**: Handles `SubclassOf`, `InstanceOf`, and `HasAttribute` queries
- **Graph Traversal**: Efficient BFS traversal with cycle detection and depth limiting
- **Confidence Scoring**: Returns confidence levels for answers
- **Rich Query Results**: Detailed execution metadata including entities visited and cache hits

### 2. Production-Ready Observability
- **Comprehensive Metrics**: Request rates, latencies, error rates, cache hit rates
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Health Checks**: Deep health monitoring for all system components
- **Performance Monitoring**: Query execution times, storage statistics, system resources

### 3. Enterprise Resilience Patterns
- **Circuit Breaker**: Automatic fault isolation and recovery
- **Intelligent Caching**: Multi-level caching with TTL and LRU eviction
- **Graceful Degradation**: Continues operation even with partial failures
- **Connection Pooling**: Efficient resource management

### 4. High-Performance Data Processing
- **Parallel CSV Ingestion**: Concurrent processing with backpressure control
- **Batch Operations**: Optimized bulk data operations
- **Memory-Efficient Streaming**: Process large datasets without memory exhaustion
- **Deduplication**: Automatic entity deduplication during ingestion

## 🔌 Storage System Integration

The system provides a pluggable storage architecture supporting multiple backends:

### In-Memory Storage (Default)
```python
from src.infrastructure.storage.memory_adapter import InMemoryStorageAdapter
from src.observability.metrics import InMemoryMetricsCollector

metrics = InMemoryMetricsCollector()
storage = InMemoryStorageAdapter(metrics)
```

### PostgreSQL Integration Example
```python
import asyncpg
from src.infrastructure.storage.interfaces import StorageAdapter

class PostgreSQLStorageAdapter(StorageAdapter):
    def __init__(self, connection_string: str, metrics: MetricsCollector):
        self.connection_string = connection_string
        self.metrics = metrics
        self.pool = None
    
    async def initialize(self):
        self.pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=5,
            max_size=20
        )
    
    async def get_entity(self, entity_id: str) -> Optional[Entity]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name, created_at, metadata FROM entities WHERE id = $1",
                entity_id
            )
            if row:
                return Entity(
                    id=row['id'],
                    name=row['name'],
                    created_at=row['created_at'],
                    metadata=row['metadata']
                )
            return None
    
    async def store_entities(self, entities: List[Entity]) -> None:
        async with self.pool.acquire() as conn:
            await conn.executemany(
                """INSERT INTO entities (id, name, created_at, metadata) 
                   VALUES ($1, $2, $3, $4) ON CONFLICT (id) DO NOTHING""",
                [(e.id, e.name, e.created_at, e.metadata) for e in entities]
            )

# Usage
storage = PostgreSQLStorageAdapter("postgresql://user:pass@localhost/ontology", metrics)
await storage.initialize()
```

### Neo4j Graph Database Integration Example
```python
from neo4j import AsyncGraphDatabase
from src.infrastructure.storage.interfaces import StorageAdapter

class Neo4jStorageAdapter(StorageAdapter):
    def __init__(self, uri: str, user: str, password: str, metrics: MetricsCollector):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        self.metrics = metrics
    
    async def get_relationships_by_head(self, head_entity: str) -> List[Relationship]:
        async with self.driver.session() as session:
            result = await session.run(
                "MATCH (h {id: $head})-[r]->(t) RETURN h.id, type(r), t.id, r.confidence",
                head=head_entity
            )
            relationships = []
            async for record in result:
                relationships.append(Relationship(
                    head_entity=record['h.id'],
                    tail_entity=record['t.id'],
                    edge_type=EdgeType(record['type(r)']),
                    confidence=record['r.confidence']
                ))
            return relationships

# Usage
storage = Neo4jStorageAdapter("bolt://localhost:7687", "neo4j", "password", metrics)
```

## 📊 Data Ingestion Integration

The system supports multiple data ingestion patterns through pluggable adapters:

### Kafka Stream Processing Integration
```python
from kafka import KafkaConsumer
from src.infrastructure.ingestion.interfaces import DataIngestionAdapter

class KafkaStreamIngestionAdapter(DataIngestionAdapter):
    def __init__(self, kafka_config: Dict[str, Any], topic: str, metrics: MetricsCollector):
        self.consumer = KafkaConsumer(
            topic,
            **kafka_config,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        self.metrics = metrics
    
    async def ingest_entities(self) -> AsyncIterator[List[Entity]]:
        batch = []
        for message in self.consumer:
            entity_data = message.value
            entity = Entity(
                id=entity_data['id'],
                name=entity_data['name'],
                metadata=entity_data.get('metadata')
            )
            batch.append(entity)
            
            if len(batch) >= self.batch_size:
                self.metrics.increment_counter("kafka_entities_processed", len(batch))
                yield batch
                batch = []

# Usage
kafka_config = {
    'bootstrap_servers': ['localhost:9092'],
    'group_id': 'ontology-consumer',
    'auto_offset_reset': 'earliest'
}
adapter = KafkaStreamIngestionAdapter(kafka_config, 'ontology-entities', metrics)
```

### Apache Spark Batch Processing Integration
```python
from pyspark.sql import SparkSession
from src.infrastructure.ingestion.interfaces import DataIngestionAdapter

class SparkBatchIngestionAdapter(DataIngestionAdapter):
    def __init__(self, spark_config: Dict[str, Any], data_path: str, metrics: MetricsCollector):
        self.spark = SparkSession.builder.appName("OntologyIngestion").getOrCreate()
        self.data_path = data_path
        self.metrics = metrics
    
    async def ingest_relationships(self) -> AsyncIterator[List[Relationship]]:
        # Read large dataset with Spark
        df = self.spark.read.parquet(self.data_path)
        
        # Process in partitions
        for partition in df.rdd.glom().collect():
            relationships = []
            for row in partition:
                rel = Relationship(
                    head_entity=row['head'],
                    tail_entity=row['tail'],
                    edge_type=EdgeType(row['edge_type']),
                    confidence=row['confidence']
                )
                relationships.append(rel)
            
            self.metrics.increment_counter("spark_relationships_processed", len(relationships))
            yield relationships

# Usage
spark_config = {"spark.sql.adaptive.enabled": "true"}
adapter = SparkBatchIngestionAdapter(spark_config, "hdfs://ontology/relationships.parquet", metrics)
```

### REST API Integration
```python
import aiohttp
from src.infrastructure.ingestion.interfaces import DataIngestionAdapter

class RestAPIIngestionAdapter(DataIngestionAdapter):
    def __init__(self, api_base_url: str, auth_token: str, metrics: MetricsCollector):
        self.api_base_url = api_base_url
        self.auth_token = auth_token
        self.metrics = metrics
    
    async def ingest_entities(self) -> AsyncIterator[List[Entity]]:
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        async with aiohttp.ClientSession(headers=headers) as session:
            offset = 0
            while True:
                async with session.get(
                    f"{self.api_base_url}/entities",
                    params={'limit': self.batch_size, 'offset': offset}
                ) as response:
                    if response.status != 200:
                        break
                    
                    data = await response.json()
                    if not data['entities']:
                        break
                    
                    entities = [
                        Entity(id=e['id'], name=e['name'], metadata=e.get('metadata'))
                        for e in data['entities']
                    ]
                    
                    self.metrics.increment_counter("api_entities_fetched", len(entities))
                    yield entities
                    offset += self.batch_size

# Usage
adapter = RestAPIIngestionAdapter("https://api.example.com", "your-token", metrics)
```

## 📈 Comprehensive Metrics

The system collects detailed metrics across all components:

### Query Performance Metrics
- `ontology_questions_total{type, result}` - Total questions processed by type and result
- `ontology_question_duration_ms` - Question processing latency histogram
- `ontology_cache_hits_total` - Cache hit counter
- `ontology_cache_misses_total` - Cache miss counter
- `ontology_max_depth_exceeded_total` - Queries hitting depth limits

### Storage Metrics
- `storage_entity_reads_total{hit}` - Entity read operations with hit/miss labels
- `storage_relationship_reads_total{type}` - Relationship queries by type
- `storage_entities_stored_total` - Entities successfully stored
- `storage_relationships_stored_total` - Relationships successfully stored
- `storage_total_entities` - Current entity count gauge
- `storage_total_relationships` - Current relationship count gauge
- `storage_errors_total{operation}` - Storage operation errors

### System Health Metrics
- `circuit_breaker_state_changes_total{to_state}` - Circuit breaker state transitions
- `storage_health_checks_total{status}` - Health check results
- `cache_evictions_total` - Cache eviction events
- `ingestion_chunks_processed_total` - Data ingestion progress
- `ingestion_validation_errors_total` - Data validation failures

### Business Logic Metrics
- `questions_processed_total{result}` - Business outcome tracking
- `questions_failed_total{error_type}` - Error categorization
- `data_loads_total{status}` - Data loading success/failure rates

## 🏃‍♂️ Quick Start

### Prerequisites
```bash
# Python 3.8+
pip install asyncio aiofiles
# Optional: For Prometheus metrics
pip install prometheus-client
# Optional: For advanced logging
pip install python-json-logger
```

### Basic Usage
```bash
# Clone and setup
git clone <repository>
cd ontology-system

# Create sample data file
mkdir -p data
cat > data/ontology.csv << EOF
HEAD_ENTITY,TAIL_ENTITY,EDGE_TYPE,CONFIDENCE
dog,animal,SubclassOf,1.0
cat,animal,SubclassOf,1.0
Fido,dog,InstanceOf,1.0
animal,living_thing,SubclassOf,0.9
university,educational,HasAttribute,1.0
EOF

# Run the system
python -m src.main
```

## 🧪 Testing

### Unit Tests
```python
import pytest
from src.application.orchestrator import OntologyOrchestrator
from src.infrastructure.storage.memory_adapter import InMemoryStorageAdapter

@pytest.mark.asyncio
async def test_question_processing():
    storage = InMemoryStorageAdapter(metrics)
    orchestrator = OntologyOrchestrator(storage)
    
    # Load test data
    # ... data setup
    
    result = await orchestrator.process_question("is dog a type of animal?")
    assert result.result == QuestionResult.YES
    assert result.confidence > 0.9
```

### Performance Benchmarks
```python
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

async def benchmark_concurrent_queries():
    """Benchmark concurrent query processing"""
    orchestrator = setup_test_orchestrator()
    
    questions = ["is dog a type of animal?"] * 100
    
    start_time = time.time()
    tasks = [orchestrator.process_question(q) for q in questions]
    results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_time
    print(f"Processed {len(results)} queries in {total_time:.2f}s")
    print(f"Average latency: {(total_time / len(results)) * 1000:.2f}ms")
```

## 🔧 Advanced Configuration

### Custom Storage Adapter
Implement the `StorageAdapter` interface for your specific needs:
```python
class CustomStorageAdapter(StorageAdapter):
    async def get_entity(self, entity_id: str) -> Optional[Entity]:
        # Your implementation
        pass
    
    async def store_entities(self, entities: List[Entity]) -> None:
        # Your implementation  
        pass
    
    # Implement all abstract methods...
```

### Custom Metrics Collector
Integrate with your monitoring infrastructure:
```python
class CustomMetricsCollector(MetricsCollector):
    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        # Send to your metrics backend
        pass
```

## 📄 License

MIT License - See LICENSE file for details.

---

*This ontology system demonstrates production-ready Python development with enterprise architecture patterns, comprehensive observability, and extensible design suitable for large-scale knowledge graph applications.*