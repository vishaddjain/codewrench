class IRNode:
    def __init__(self, node_type, lineno, children=None, metadata=None):
        self.node_type = node_type
        self.lineno = lineno
        self.children = children or []
        self.metadata = metadata or {}

    def __repr__(self):
        return f"IRNode({self.node_type}, line={self.lineno})"

        