class Orchestrator:
    """Much simpler orchestrator focused on coordination"""
    
    def __init__(self, service_factory: ServiceFactory):
        self.service_factory = service_factory
        self.reasoning_coordinator = service_factory.create_reasoning_coordinator()
        self.entity_validator = service_factory.create_entity_validator()
        self.question_parser = QuestionParser()
    
    async def process_question(self, question_text: str) -> QueryResult:
        """Process question with minimal coordination logic"""
        # Parse question
        question = self.question_parser.parse(question_text)
        
        # Validate entities exist
        if not await self.entity_validator.entities_exist(question.head, question.tail):
            return QueryResult(
                result=QuestionResult.DONT_KNOW,
                confidence=0.0,
                execution_time_ms=0,
                entities_visited=0,
                explanation=f"Entities not found: {question.head}, {question.tail}",
                request_id=question.request_id
            )
        
        # Delegate to reasoning coordinator
        return await self.reasoning_coordinator.answer_question(question)