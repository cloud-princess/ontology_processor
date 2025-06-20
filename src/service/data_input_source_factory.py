# Factory for creating input sources
class InputSourceFactory:
    """Factory for creating input sources based on configuration."""
    
    @staticmethod
    def create_source(input_type: InputType, source_id: str, config: Dict[str, Any]) -> InputSource:
        """Create an input source based on type and configuration."""
        if input_type == InputType.BATCH_CSV:
            return CSVInputSource(source_id, config)
        elif input_type == InputType.STREAM_REALTIME:
            return StreamInputSource(source_id, config)
        elif input_type == InputType.DATABASE_POLL:
            return DatabaseInputSource(source_id, config)
        elif input_type == InputType.RESEARCH_BATCH:
            return ResearchBatchInputSource(source_id, config)
        else:
            raise ValueError(f"Unsupported input type: {input_type}")