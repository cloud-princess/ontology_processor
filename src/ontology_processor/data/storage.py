"""
Storage adapter implementations for different backends.
Demonstrates database abstraction and scalability patterns.
"""
import logging
from typing import List, Dict, Any, Optional
import asyncio
import json
from datetime import datetime

from .interfaces import DataStorageAdapter
from ..core.models import Edge, EdgeType

logger = logging.getLogger(__name__)


class PostgreSQLAdapter(DataStorageAdapter):
    """
    PostgreSQL adapter for ACID compliance and complex queries.
    Suitable for moderate scale with strong consistency requirements.
    """
    
    def __init__(self):
        self.connection = None
        self.connection_pool = None
    
    async def connect(self, connection_string: str) -> None:
        """Establish connection pool for efficiency."""
        try:
            # In practice, use asyncpg for PostgreSQL connections
            logger.info(f"Connecting to PostgreSQL: {connection_string}")
            # self.connection_pool = await asyncpg.create_pool(connection_string)
            self.connection = "mock_postgres_connection"
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close connection pool."""
        if self.connection_pool:
            # await self.connection_pool.close()
            pass
        self.connection = None
    
    async def store_edges(self, edges: List[Edge]) -> None:
        """
        Store edges using batch insert for efficiency.
        Implements the pattern from Chapter 3 of DDIA - Storage and Retrieval.
        """
        if not self.connection:
            raise RuntimeError("Not connected to database")
        
        try:
            # Prepare batch insert
            values = []
            for edge in edges:
                values.append({
                    'edge_type': edge.edge_type.value,
                    'head_entity': edge.head_entity,
                    'tail_entity': edge.tail_entity,
                    'confidence': edge.confidence,
                    'metadata': json.dumps(edge.metadata) if edge.metadata else None,
                    'created_at': datetime.now()
                })
            
            # In practice, execute batch insert
            logger.info(f"Storing {len(edges)} edges to PostgreSQL")
            # await self.connection_pool.executemany(INSERT_QUERY, values)
            
        except Exception as e:
            logger.error(f"Failed to store edges: {e}")
            raise
    
    async def retrieve_edges(self, query: Dict[str, Any]) -> List[Edge]:
        """Retrieve edges with optimized queries."""
        if not self.connection:
            raise RuntimeError("Not connected to database")
        
        # Build dynamic query based on filters
        where_clauses = []
        params = []
        
        if 'head_entity' in query:
            where_clauses.append("head_entity = $%d" % (len(params) + 1))
            params.append(query['head_entity'])
        
        if 'edge_type' in query:
            where_clauses.append("edge_type = $%d" % (len(params) + 1))
            params.append(query['edge_type'])
        
        # Execute query and return results
        logger.info(f"Retrieving edges with query: {query}")
        return []  # Placeholder
    
    async def health_check(self) -> bool:
        """
        Check if PostgreSQL backend is healthy.
        Implements health check pattern for reliability (DDIA Chapter 8).
        """
        try:
            async with self._get_connection() as conn:
                result = await conn.fetchval("SELECT 1")
                return result == 1
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return False


class Neo4jAdapter(DataStorageAdapter):
    """
    Neo4j adapter for graph-native storage and complex relationship queries.
    Optimized for graph traversals and pattern matching.
    
    Design Principles Applied (from DDIA):
    - Chapter 2: Graph data model for complex relationships
    - Chapter 3: Native graph storage for efficient traversals
    - Chapter 5: Batch operations with Cypher transactions
    """
    
    def __init__(self, max_connection_lifetime: int = 3600, max_connection_pool_size: int = 100):
        self.driver = None
        self.max_connection_lifetime = max_connection_lifetime
        self.max_connection_pool_size = max_connection_pool_size
        self._is_connected = False
    
    async def connect(self, connection_string: str) -> None:
        """
        Establish Neo4j driver connection.
        Uses connection pooling for efficiency.
        """
        try:
            from neo4j import AsyncGraphDatabase
            
            # Parse connection string to extract auth info
            # Format: neo4j://username:password@host:port
            if '@' in connection_string:
                auth_part, host_part = connection_string.split('@')
                protocol_user_pass = auth_part.split('//')[-1]
                username, password = protocol_user_pass.split(':')
                uri = connection_string.split('@')[0].replace(protocol_user_pass, '') + '@' + host_part
                auth = (username, password)
            else:
                uri = connection_string
                auth = None
            
            logger.info(f"Establishing Neo4j connection to {uri}")
            self.driver = AsyncGraphDatabase.driver(
                uri,
                auth=auth,
                max_connection_lifetime=self.max_connection_lifetime,
                max_connection_pool_size=self.max_connection_pool_size,
                encrypted=False  # Set to True for production
            )
            
            # Verify connection
            await self.health_check()
            self._is_connected = True
            logger.info("Neo4j connection established successfully")
            
        except ImportError:
            logger.error("neo4j driver not installed. Run: pip install neo4j")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close Neo4j driver connection."""
        if self.driver:
            logger.info("Closing Neo4j driver connection")
            await self.driver.close()
            self.driver = None
            self._is_connected = False
    
    async def store_edges(self, edges: List[Edge]) -> None:
        """
        Store edges as graph relationships in Neo4j.
        Uses Cypher batch operations for efficiency (DDIA Chapter 5).
        """
        if not edges:
            return
        
        if not self._is_connected:
            raise RuntimeError("Not connected to Neo4j. Call connect() first.")
        
        async with self.driver.session() as session:
            try:
                # Use transaction for atomicity
                async with session.begin_transaction() as tx:
                    # Batch create nodes and relationships
                    for edge in edges:
                        # Create or update entities as nodes
                        await tx.run(
                            """
                            MERGE (head:Entity {name: $head_name})
                            MERGE (tail:Entity {name: $tail_name})
                            """,
                            head_name=edge.head_entity,
                            tail_name=edge.tail_entity
                        )
                        
                        # Create relationship with properties
                        relationship_type = edge.edge_type.value.upper().replace(' ', '_')
                        await tx.run(
                            f"""
                            MATCH (head:Entity {{name: $head_name}})
                            MATCH (tail:Entity {{name: $tail_name}})
                            MERGE (head)-[r:{relationship_type}]->(tail)
                            SET r.confidence = $confidence,
                                r.metadata = $metadata,
                                r.updated_at = datetime()
                            """,
                            head_name=edge.head_entity,
                            tail_name=edge.tail_entity,
                            confidence=edge.confidence,
                            metadata=json.dumps(edge.metadata) if edge.metadata else None
                        )
                    
                    await tx.commit()
                    logger.info(f"Successfully stored {len(edges)} edges to Neo4j")
                    
            except Exception as e:
                logger.error(f"Failed to store edges in Neo4j: {e}")
                raise
    
    async def retrieve_edges(self, query: Dict[str, Any]) -> List[Edge]:
        """
        Retrieve edges using Cypher pattern matching.
        Leverages Neo4j's native graph traversal capabilities.
        """
        if not self._is_connected:
            raise RuntimeError("Not connected to Neo4j. Call connect() first.")
        
        async with self.driver.session() as session:
            try:
                # Build Cypher query based on filters
                cypher_query = "MATCH (head:Entity)-[r]->(tail:Entity)"
                where_clauses = []
                params = {}
                
                if 'head_entity' in query:
                    where_clauses.append("head.name = $head_name")
                    params['head_name'] = query['head_entity']
                
                if 'tail_entity' in query:
                    where_clauses.append("tail.name = $tail_name")
                    params['tail_name'] = query['tail_entity']
                
                if 'edge_type' in query:
                    relationship_type = query['edge_type'].upper().replace(' ', '_')
                    cypher_query = f"MATCH (head:Entity)-[r:{relationship_type}]->(tail:Entity)"
                
                if 'min_confidence' in query:
                    where_clauses.append("r.confidence >= $min_confidence")
                    params['min_confidence'] = query['min_confidence']
                
                if where_clauses:
                    cypher_query += " WHERE " + " AND ".join(where_clauses)
                
                cypher_query += " RETURN head.name as head_entity, tail.name as tail_entity, type(r) as edge_type, r.confidence as confidence, r.metadata as metadata"
                
                if 'limit' in query:
                    cypher_query += " LIMIT $limit"
                    params['limit'] = query['limit']
                
                # Execute query
                result = await session.run(cypher_query, **params)
                records = await result.data()
                
                # Convert records to Edge objects
                edges = []
                for record in records:
                    try:
                        edge_type_str = record['edge_type'].lower().replace('_', ' ')
                        edge = Edge(
                            edge_type=EdgeType(edge_type_str),
                            head_entity=record['head_entity'],
                            tail_entity=record['tail_entity'],
                            confidence=record.get('confidence', 1.0),
                            metadata=json.loads(record['metadata']) if record.get('metadata') else None
                        )
                        edges.append(edge)
                    except Exception as e:
                        logger.warning(f"Failed to parse edge from record: {e}")
                        continue
                
                logger.info(f"Retrieved {len(edges)} edges from Neo4j")
                return edges
                
            except Exception as e:
                logger.error(f"Failed to retrieve edges from Neo4j: {e}")
                raise
    
    async def health_check(self) -> bool:
        """
        Check if Neo4j backend is healthy.
        Verifies both connectivity and database responsiveness.
        """
        try:
            if not self.driver:
                return False
            
            async with self.driver.session() as session:
                result = await session.run("RETURN 1 as health_check")
                record = await result.single()
                return record['health_check'] == 1
                
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            return False


class InMemoryAdapter(DataStorageAdapter):
    """
    In-memory storage adapter for testing and development.
    Not suitable for production but useful for rapid prototyping.
    
    Design Principles Applied:
    - Simplicity for development/testing environments
    - Fast access patterns for small datasets
    """
    
    def __init__(self):
        self.edges: List[Edge] = []
        self._is_connected = False
    
    async def connect(self, connection_string: str) -> None:
        """Initialize in-memory storage."""
        logger.info("Initializing in-memory storage")
        self.edges = []
        self._is_connected = True
    
    async def disconnect(self) -> None:
        """Clear in-memory storage."""
        logger.info("Clearing in-memory storage")
        self.edges = []
        self._is_connected = False
    
    async def store_edges(self, edges: List[Edge]) -> None:
        """Store edges in memory with deduplication."""
        if not self._is_connected:
            raise RuntimeError("Not connected. Call connect() first.")
        
        # Simple deduplication based on edge properties
        existing_edges = {(e.edge_type, e.head_entity, e.tail_entity) for e in self.edges}
        
        new_edges = []
        updated_count = 0
        
        for edge in edges:
            edge_key = (edge.edge_type, edge.head_entity, edge.tail_entity)
            if edge_key in existing_edges:
                # Update existing edge
                for i, existing_edge in enumerate(self.edges):
                    if (existing_edge.edge_type, existing_edge.head_entity, existing_edge.tail_entity) == edge_key:
                        self.edges[i] = edge
                        updated_count += 1
                        break
            else:
                new_edges.append(edge)
        
        self.edges.extend(new_edges)
        logger.info(f"Stored {len(new_edges)} new edges, updated {updated_count} existing edges in memory")
    
    async def retrieve_edges(self, query: Dict[str, Any]) -> List[Edge]:
        """Retrieve edges from memory with filtering."""
        if not self._is_connected:
            raise RuntimeError("Not connected. Call connect() first.")
        
        filtered_edges = self.edges
        
        # Apply filters
        if 'head_entity' in query:
            filtered_edges = [e for e in filtered_edges if e.head_entity == query['head_entity']]
        
        if 'tail_entity' in query:
            filtered_edges = [e for e in filtered_edges if e.tail_entity == query['tail_entity']]
        
        if 'edge_type' in query:
            filtered_edges = [e for e in filtered_edges if e.edge_type == EdgeType(query['edge_type'])]
        
        if 'min_confidence' in query:
            filtered_edges = [e for e in filtered_edges if e.confidence >= query['min_confidence']]
        
        # Apply limit
        if 'limit' in query:
            filtered_edges = filtered_edges[:query['limit']]
        
        logger.info(f"Retrieved {len(filtered_edges)} edges from memory")
        return filtered_edges
    
    async def health_check(self) -> bool:
        """Always healthy for in-memory storage."""
        return self._is_connected