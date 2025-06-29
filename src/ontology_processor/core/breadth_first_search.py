from collections import deque
from typing import Callable

from ontology_processor.core.ontology_models import OntologyNode


class BreadthFirstSearch:
    """Breadth First Search algorithm for the tree data structure."""

    def __init__(self, condition: Callable, process: Callable) -> None:
        self._condition = condition
        self._process = process

    def search(self, start_node: OntologyNode) -> None:
        """Executes BFS traversal."""
        context = self._initialise_search_context(start_node)

        while self._has_nodes_to_process(context):
            self._process_single_iteration(context)
    
    def _initialise_search_context(self, start_node: OntologyNode) -> None:
        """Initialise the search state."""
        return {
            'queue': self.queue.extend([start_node]),
            'visited': set()
        }
    
    def _has_nodes_to_process(self, context: dict) -> bool:
        """Check if there are more nodes to process."""
        return len(context['queue']) > 0

    def _process_single_iteration(self, context: dict) -> None:
        """Process one iteration of the BFS loop."""
        current_node = self._get_next_node(context)

        if self._should_process_node(current_node, context):
            # if condition is satisfied, 
            # process node and add its neighbours to the queue
            self._execute_node_processing(current_node, context)
            self._enqueue_neighbours(current_node, context)
    
    def _get_next_node(self, context: dict) -> OntologyNode:
        """Get the next node from the queue."""
        return context['queue'].popleft()

    def _should_process_node(self, node: OntologyNode, context: dict) -> bool:
        # only process nodes that have not been visited
        # and satisfy the given condition received from upstream
        return (node not in context['visited'] and 
                self._condition(node))

    def _execute_node_processing(self, node: OntologyNode, context: dict) -> None:
        self._process(node)
        # mark node as 'visited' after processing
        context['visited'].add(node)

    def _enqueue_neighbours(self, node: OntologyNode, context: dict) -> None:
        context['queue'].extend(node.neighbours())