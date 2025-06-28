class Edge:
    """Object representing an edge in a directed graph."""
    def __init__(self, edge_type: str, head_entity: str, tail_entity: str) -> None:
        self.edge_type = edge_type
        self.head_entity = head_entity
        self.tail_entity = tail_entity


class GraphNode:
    """Object representing a node in a directed graph."""
    def __init__(self) -> None:
        self.outgoing_edges: List[Edge] = []
        self.incoming_edges: List[Edge] = []

    def add_outgoing_edge(self, edge: Edge):
        self.outgoing_edges.append(edge)
    
    def add_incoming_edge(self, edge: Edge):
        self.incoming_edges.append(edge)
    
    def get_neighbours_by_edge_type(self, edge_type: str) -> List[GraphNode]:
        pass