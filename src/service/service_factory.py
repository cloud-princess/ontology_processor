class ServiceFactory:
    """Factory for creating and wiring up services"""
    
    def __init__(self, storage_adapter: StorageAdapter, cache_adapter: Optional[CacheAdapter] = None,
                 metrics: Optional[MetricsCollector] = None):
        self.storage_adapter = storage_adapter
        self.cache_adapter = cache_adapter
        self.metrics = metrics
    
    def create_reasoning_coordinator(self) -> ReasoningCoordinator:
        """Create fully configured reasoning coordinator"""
        # Create supporting services
        storage_service = StorageService(self.storage_adapter)
        cache_service = QueryCacheService(self.cache_adapter)
        traversal_service = TraversalService(storage_service)
        
        # Create reasoning strategies
        hierarchy_reasoner = HierarchyReasoner(traversal_service)
        attribute_reasoner = AttributeReasoner(storage_service, hierarchy_reasoner)
        
        # Create and configure coordinator
        coordinator = ReasoningCoordinator(cache_service)
        coordinator.register_strategy(QuestionType.SUBCLASS_OF, hierarchy_reasoner)
        coordinator.register_strategy(QuestionType.INSTANCE_OF, hierarchy_reasoner)
        coordinator.register_strategy(QuestionType.HAS_ATTRIBUTE, attribute_reasoner)
        
        return coordinator
    
    def create_entity_validator(self) -> EntityValidator:
        """Create entity validator"""
        storage_service = StorageService(self.storage_adapter)
        return EntityValidator(storage_service)