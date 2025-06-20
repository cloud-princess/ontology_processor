from collections import deque
from typing import Tuple, Set
from src.domain.models import QuestionResult, EdgeType, ExecutionContext, QueryMetrics
import time

class TraversalService:
    """Focused service for graph traversal operations"""
    
    def __init__(self, storage_service: 'StorageService'):
        self.storage_service = storage_service
    
    async def find_path(self, start: str, target: str, edge_type: EdgeType, 
                       context: ExecutionContext) -> Tuple[QuestionResult, QueryMetrics]:
        """BFS path finding with metrics tracking"""
        start_time = time.time()
        queue = deque([(start, 0)])
        visited = {start}
        entities_visited = 0
        first_iteration = True
        
        while queue:
            current, depth = queue.popleft()
            entities_visited += 1
            
            if depth > context.max_depth:
                break
            
            if time.time() - start_time > context.timeout_seconds:
                break
            
            relationships = await self.storage_service.get_relationships_by_head(current)
            
            # Check for mutual exclusivity
            if await self._check_mutual_exclusivity(relationships, target):
                metrics = QueryMetrics(
                    execution_time_ms=(time.time() - start_time) * 1000,
                    entities_visited=entities_visited,
                    cache_hit=False,
                    depth_reached=depth
                )
                return QuestionResult.NO, metrics
            
            # Get relevant relationships
            relevant_rels = self._filter_relevant_relationships(
                relationships, edge_type, first_iteration
            )
            first_iteration = False
            
            for rel in relevant_rels:
                if rel.tail_entity == target:
                    metrics = QueryMetrics(
                        execution_time_ms=(time.time() - start_time) * 1000,
                        entities_visited=entities_visited,
                        cache_hit=False,
                        depth_reached=depth
                    )
                    return QuestionResult.YES, metrics
                
                if rel.tail_entity not in visited:
                    visited.add(rel.tail_entity)
                    queue.append((rel.tail_entity, depth + 1))
        
        metrics = QueryMetrics(
            execution_time_ms=(time.time() - start_time) * 1000,
            entities_visited=entities_visited,
            cache_hit=False,
            depth_reached=depth if queue else context.max_depth
        )
        return QuestionResult.DONT_KNOW, metrics
    
    async def _check_mutual_exclusivity(self, relationships, target: str) -> bool:
        """Check if target is mutually exclusive"""
        mutex_targets = {rel.tail_entity for rel in relationships 
                        if rel.edge_type == EdgeType.MUTUALLY_EXCLUSIVE}
        return target in mutex_targets
    
    def _filter_relevant_relationships(self, relationships, edge_type: EdgeType, 
                                     first_iteration: bool) -> list:
        """Filter relationships based on edge type and iteration"""
        if first_iteration and edge_type == EdgeType.INSTANCE_OF:
            return [rel for rel in relationships if rel.edge_type == EdgeType.INSTANCE_OF]
        else:
            return [rel for rel in relationships if rel.edge_type == EdgeType.SUBCLASS_OF]
