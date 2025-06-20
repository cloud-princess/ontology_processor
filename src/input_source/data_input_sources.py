class CSVInputSource(InputSource):
    """CSV file input source for batch processing."""
    
    async def read_questions(self) -> AsyncIterator[QuestionInput]:
        file_path = Path(self.config["file_path"])
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield QuestionInput(
                    question_id=row.get("id", str(uuid.uuid4())),
                    question_text=row["question"],
                    priority=Priority(int(row.get("priority", Priority.NORMAL.value))),
                    source=self.source_id,
                    metadata={"row_data": row}
                )
    
    async def health_check(self) -> bool:
        return Path(self.config["file_path"]).exists()
    
class StreamInputSource(InputSource):
    """Real-time stream input source (simulated for demo)."""
    
    def __init__(self, source_id: str, config: Dict[str, Any]):
        super().__init__(source_id, config)
        self._queue = asyncio.Queue(maxsize=config.get("buffer_size", 1000))
    
    async def add_question(self, question: str, priority: Priority = Priority.NORMAL):
        """Add a question to the stream (simulates external system)."""
        question_input = QuestionInput(
            question_id=str(uuid.uuid4()),
            question_text=question,
            priority=priority,
            source=self.source_id
        )
        await self._queue.put(question_input)
    
    async def read_questions(self) -> AsyncIterator[QuestionInput]:
        while True:
            try:
                question = await asyncio.wait_for(
                    self._queue.get(), 
                    timeout=self.config.get("timeout_seconds", 1.0)
                )
                yield question
            except asyncio.TimeoutError:
                # No questions available, continue polling
                continue
    
    async def health_check(self) -> bool:
        return True

class DatabaseInputSource(InputSource):
    """Database polling input source."""
    
    async def read_questions(self) -> AsyncIterator[QuestionInput]:
        # Simulated database polling
        poll_interval = self.config.get("poll_interval_seconds", 5)
        
        while True:
            # In real implementation, this would query actual database
            questions = await self._poll_database()
            for question in questions:
                yield question
            
            await asyncio.sleep(poll_interval)
    
    async def _poll_database(self) -> List[QuestionInput]:
        """Simulate database polling."""
        # In production, this would use actual database connection
        return []
    
    async def health_check(self) -> bool:
        # In production, this would check database connectivity
        return True

class ResearchBatchInputSource(InputSource):
    """High-throughput batch source for research workloads."""
    
    async def read_questions(self) -> AsyncIterator[QuestionInput]:
        batch_size = self.config.get("batch_size", 10000)
        file_path = Path(self.config["file_path"])
        
        questions_batch = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    question = QuestionInput(
                        question_id=data.get("id", f"research_{line_num}"),
                        question_text=data["question"],
                        priority=Priority.LOW,  # Research workloads typically lower priority
                        source=self.source_id,
                        metadata={"batch_id": data.get("batch_id"), "experiment": data.get("experiment")}
                    )
                    questions_batch.append(question)
                    
                    if len(questions_batch) >= batch_size:
                        for q in questions_batch:
                            yield q
                        questions_batch = []
                
                except json.JSONDecodeError:
                    self.logger.warning(f"Skipping invalid JSON on line {line_num}")
        
        # Yield remaining questions
        for q in questions_batch:
            yield q
    
    async def health_check(self) -> bool:
        return Path(self.config["file_path"]).exists()