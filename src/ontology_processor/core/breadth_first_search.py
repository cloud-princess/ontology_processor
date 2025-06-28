from collections import deque
from typing import Callable

from ontology_processor.core.ontology_models import OntologyNode


class BreadthFirstSearch:
    """Breadth First Search algorithm for the tree data structure."""

    def __init__(self, condition: Callable, process: Callable) -> None:
        self.condition = condition
        self.process = process
        self.visited = set()

    def bfs(self, node: OntologyNode) -> None:
        queue = deque([node])
        visited.add(node)

        while queue:
            current_node = queue.popleft()
            self.process(current_node)

            if not current_node.visited and self.condition(current_node) is True:
                queue.extend(current_node.neighbours())
                visited.add(current_node)
