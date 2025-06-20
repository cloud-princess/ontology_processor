from abc import ABC, abstractmethod
from typing import Tuple
from src.domain.models import Question, QuestionResult, ExecutionContext, QueryMetrics

class ReasoningStrategy(ABC):
    """Strategy pattern for different reasoning approaches"""
    
    @abstractmethod
    async def reason(self, question: Question, context: ExecutionContext) -> Tuple[QuestionResult, QueryMetrics]:
        pass

class HierarchyReasoner(ReasoningStrategy):
    """Handles subclass/instance relationships"""
    
    def __init__(self, traversal_service: 'TraversalService'):
        self.traversal_service = traversal_service
    
    async def reason(self, question: Question, context: ExecutionContext) -> Tuple[QuestionResult, QueryMetrics]:
        if question.head == question.tail:
            result = QuestionResult.YES if question.question_type == QuestionType.SUBCLASS_OF else QuestionResult.NO
            return result, QueryMetrics(execution_time_ms=0, entities_visited=0, cache_hit=False)
        
        edge_type = EdgeType.SUBCLASS_OF if question.question_type == QuestionType.SUBCLASS_OF else EdgeType.INSTANCE_OF
        return await self.traversal_service.find_path(question.head, question.tail, edge_type, context)

class AttributeReasoner(ReasoningStrategy):
    """Handles attribute relationships"""
    
    def __init__(self, storage_service: 'StorageService', hierarchy_reasoner: HierarchyReasoner):
        self.storage_service = storage_service
        self.hierarchy_reasoner = hierarchy_reasoner
    
    async def reason(self, question: Question, context: ExecutionContext) -> Tuple[QuestionResult, QueryMetrics]:
        start_time = time.time()
        entities_visited = 0
        
        # Get direct attribute relationships
        attribute_relationships = await self.storage_service.get_relationships_by_tail(question.tail)
        entities_visited += 1
        
        attribute_parents = {rel.head_entity for rel in attribute_relationships 
                           if rel.edge_type == EdgeType.HAS_ATTRIBUTE}
        
        if question.head in attribute_parents:
            metrics = QueryMetrics(
                execution_time_ms=(time.time() - start_time) * 1000,
                entities_visited=entities_visited,
                cache_hit=False
            )
            return QuestionResult.YES, metrics
        
        # Check through hierarchy
        for parent in attribute_parents:
            hierarchy_question = Question(
                question_type=QuestionType.SUBCLASS_OF,
                head=question.head,
                tail=parent,
                raw_question=""
            )
            result, sub_metrics = await self.hierarchy_reasoner.reason(hierarchy_question, context)
            entities_visited += sub_metrics.entities_visited
            
            if result == QuestionResult.YES:
                metrics = QueryMetrics(
                    execution_time_ms=(time.time() - start_time) * 1000,
                    entities_visited=entities_visited,
                    cache_hit=False
                )
                return QuestionResult.YES, metrics
        
        metrics = QueryMetrics(
            execution_time_ms=(time.time() - start_time) * 1000,
            entities_visited=entities_visited,
            cache_hit=False
        )
        return QuestionResult.DONT_KNOW, metrics