from typing import Dict, Type
from src.domain.services.reasoning import ReasoningStrategy, HierarchyReasoner, AttributeReasoner
from src.domain.models import Question, QuestionType, QuestionResult, ExecutionContext, QueryResult
from src.application.services.caching import QueryCacheService
import time

class ReasoningCoordinator:
    """Coordinates different reasoning strategies"""
    
    def __init__(self, cache_service: QueryCacheService):
        self.cache_service = cache_service
        self.strategies: Dict[QuestionType, ReasoningStrategy] = {}
    
    def register_strategy(self, question_type: QuestionType, strategy: ReasoningStrategy):
        """Register a reasoning strategy for a question type"""
        self.strategies[question_type] = strategy
    
    async def answer_question(self, question: Question) -> QueryResult:
        """Coordinate the answering of a question"""
        start_time = time.time()
        
        # Check cache first
        cached_result = await self.cache_service.get_cached_result(question)
        if cached_result:
            return QueryResult(
                result=cached_result,
                confidence=1.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                entities_visited=0,
                cache_hit=True,
                request_id=question.request_id
            )
        
        # Get appropriate strategy
        strategy = self.strategies.get(question.question_type)
        if not strategy:
            return self._create_unknown_result(question, start_time)
        
        # Execute reasoning
        context = ExecutionContext(
            start_time=start_time,
            request_id=question.request_id
        )
        
        result, metrics = await strategy.reason(question, context)
        
        # Cache the result
        await self.cache_service.cache_result(question, result)
        
        return QueryResult(
            result=result,
            confidence=0.95,
            execution_time_ms=metrics.execution_time_ms,
            entities_visited=metrics.entities_visited,
            cache_hit=metrics.cache_hit,
            request_id=question.request_id
        )
    
    def _create_unknown_result(self, question: Question, start_time: float) -> QueryResult:
        """Create result for unknown question types"""
        return QueryResult(
            result=QuestionResult.DONT_KNOW,
            confidence=0.0,
            execution_time_ms=(time.time() - start_time) * 1000,
            entities_visited=0,
            cache_hit=False,
            explanation="Unknown question type",
            request_id=question.request_id
        )