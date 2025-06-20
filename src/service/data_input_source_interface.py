# Input Source Abstractions
class InputSource(ABC):
    """Abstract base class for all input sources."""
    
    def __init__(self, source_id: str, config: Dict[str, Any]):
        self.source_id = source_id
        self.config = config
        self.logger = logging.getLogger(f"input.{source_id}")
    
    @abstractmethod
    async def read_questions(self) -> AsyncIterator[QuestionInput]:
        """Read questions from the input source."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the input source is healthy."""
        pass