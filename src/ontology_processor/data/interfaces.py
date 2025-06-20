"""
Data layer interfaces following the Repository and Strategy patterns.
Enables pluggable data sources and storage backends for scalability.
"""
from abc import ABC, abstractmethod
from typing import Iterator, List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
from ..core.models import Edge


class DataSourceType(Enum):
    """Types of data sources supported."""
    CSV_FILE = "csv_file"
    JSON_FILE = "json_file"
    DATABASE = "database"
    STREAM = "stream"
    API = "api"


@dataclass
class DataSourceConfig:
    """Configuration for data sources."""
    source_type: DataSourceType
    connection_string: str
    batch_size: int = 1000
    retry_count: int = 3
    timeout_seconds: int = 30
    metadata: Optional[Dict[str, Any]] = None


class DataIngestionStrategy(ABC):
    """
    Abstract strategy for data ingestion.
    Supports different ingestion patterns (batch, streaming, etc.)
    """
    
    @abstractmethod
    async def ingest(self, config: DataSourceConfig) -> Iterator[List[Edge]]:
        """
        Ingest data from source, yielding batches of edges.
        Uses async iterator for backpressure control.
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: DataSourceConfig) -> bool:
        """Validate configuration for this strategy."""
        pass


class DataStorageAdapter(ABC):
    """
    Abstract adapter for different storage backends.
    Follows the Adapter pattern for database abstraction.
    """
    
    @abstractmethod
    async def connect(self, connection_string: str) -> None:
        """Establish connection to storage backend."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to storage backend."""
        pass
    
    @abstractmethod
    async def store_edges(self, edges: List[Edge]) -> None:
        """Store edges in batch for efficiency."""
        pass
    
    @abstractmethod
    async def retrieve_edges(self, query: Dict[str, Any]) -> List[Edge]:
        """Retrieve edges based on query criteria."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if storage backend is healthy."""
        pass
