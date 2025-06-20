"""
Concrete implementations of data ingestion strategies.
Demonstrates different patterns from "Designing Data-Intensive Applications".
"""
import csv
import json
import logging
from typing import Iterator, List, Dict, Any
import aiofiles
import asyncio
from pathlib import Path

from .interfaces import DataIngestionStrategy, DataSourceConfig, DataSourceType
from ..core.models import Edge, EdgeType

logger = logging.getLogger(__name__)


class CSVFileIngestionStrategy(DataIngestionStrategy):
    """
    CSV file ingestion with streaming processing.
    Implements backpressure handling and memory-efficient processing.
    """
    
    async def ingest(self, config: DataSourceConfig) -> Iterator[List[Edge]]:
        """
        Stream CSV data in batches to avoid memory issues.
        Implements the pattern from Chapter 1 of DDIA - reliability through graceful degradation.
        """
        if not self.validate_config(config):
            raise ValueError("Invalid configuration for CSV ingestion")
        
        file_path = Path(config.connection_string)
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        batch: List[Edge] = []
        batch_size = config.batch_size
        
        try:
            async with aiofiles.open(file_path, mode='r', encoding='utf-8') as file:
                content = await file.read()
                reader = csv.DictReader(content.splitlines())
                
                for row_num, row in enumerate(reader, start=1):
                    try:
                        edge = self._parse_csv_row(row, row_num)
                        if edge:
                            batch.append(edge)
                        
                        if len(batch) >= batch_size:
                            yield batch
                            batch = []
                            # Yield control to allow other coroutines to run
                            await asyncio.sleep(0)
                    
                    except Exception as e:
                        logger.warning(f"Failed to parse row {row_num}: {e}")
                        # Continue processing other rows (fault tolerance)
                        continue
                
                # Yield remaining batch
                if batch:
                    yield batch
                    
        except Exception as e:
            logger.error(f"CSV ingestion failed: {e}")
            raise
    
    def validate_config(self, config: DataSourceConfig) -> bool:
        """Validate CSV-specific configuration."""
        return (config.source_type == DataSourceType.CSV_FILE and
                bool(config.connection_string) and
                config.batch_size > 0)
    
    def _parse_csv_row(self, row: Dict[str, str], row_num: int) -> Optional[Edge]:
        """Parse a CSV row into an Edge object with validation."""
        try:
            # Expected columns: Edge Type, Head Entity, Tail Entity
            edge_type_str = row.get('Edge Type', '').strip()
            head_entity = row.get('Head Entity', '').strip()
            tail_entity = row.get('Tail Entity', '').strip()
            
            if not all([edge_type_str, head_entity, tail_entity]):
                logger.warning(f"Row {row_num}: Missing required fields")
                return None
            
            # Parse edge type
            try:
                edge_type = EdgeType(edge_type_str)
            except ValueError:
                logger.warning(f"Row {row_num}: Unknown edge type '{edge_type_str}'")
                return None
            
            # Parse confidence if available
            confidence = 1.0
            if 'Confidence' in row:
                try:
                    confidence = float(row['Confidence'])
                except ValueError:
                    logger.warning(f"Row {row_num}: Invalid confidence value")
            
            return Edge(
                edge_type=edge_type,
                head_entity=head_entity,
                tail_entity=tail_entity,
                confidence=confidence,
                metadata={'source_row': row_num}
            )
            
        except Exception as e:
            logger.error(f"Failed to parse CSV row {row_num}: {e}")
            return None


class StreamingIngestionStrategy(DataIngestionStrategy):
    """
    Streaming data ingestion for real-time processing.
    Implements patterns from Chapter 11 of DDIA - Stream Processing.
    """
    
    def __init__(self, stream_processor=None):
        self.stream_processor = stream_processor
    
    async def ingest(self, config: DataSourceConfig) -> Iterator[List[Edge]]:
        """
        Process streaming data with windowing and backpressure.
        Implements micro-batching for efficiency.
        """
        if not self.validate_config(config):
            raise ValueError("Invalid configuration for streaming ingestion")
        
        # Simulated streaming source - in practice, this would be Kafka, Pulsar, etc.
        batch: List[Edge] = []
        batch_size = config.batch_size
        
        # TODO: Implement actual streaming connection
        # This is a placeholder for demonstration
        logger.info("Starting streaming ingestion (placeholder implementation)")
        
        while True:
            try:
                # In real implementation, this would read from stream
                await asyncio.sleep(1)  # Simulate streaming delay
                
                # Process accumulated batch
                if batch:
                    yield batch
                    batch = []
                
            except Exception as e:
                logger.error(f"Streaming ingestion error: {e}")
                # Implement circuit breaker pattern here
                await asyncio.sleep(5)  # Backoff before retry
    
    def validate_config(self, config: DataSourceConfig) -> bool:
        """Validate streaming-specific configuration."""
        return (config.source_type == DataSourceType.STREAM and
                bool(config.connection_string))


class BatchIngestionStrategy(DataIngestionStrategy):
    """
    Batch processing strategy for large datasets.
    Implements patterns from Chapter 10 of DDIA - Batch Processing.
    """
    
    async def ingest(self, config: DataSourceConfig) -> Iterator[List[Edge]]:
        """
        Process data in large batches for efficiency.
        Optimized for throughput over latency.
        """
        if not self.validate_config(config):
            raise ValueError("Invalid configuration for batch ingestion")
        
        # Determine appropriate strategy based on file type
        if config.connection_string.endswith('.csv'):
            csv_strategy = CSVFileIngestionStrategy()
            async for batch in csv_strategy.ingest(config):
                yield batch
        else:
            raise NotImplementedError(f"Batch ingestion not implemented for: {config.connection_string}")
    
    def validate_config(self, config: DataSourceConfig) -> bool:
        """Validate batch-specific configuration."""
        return bool(config.connection_string)