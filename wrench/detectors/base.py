class BaseDetectors:
    def __init__(self):
        self.depth = 0
        self.warnings = []
        self.attr_counts = {}
        self.global_vars = set()

    def visit(self, node):
        method = f"visit_{node.node_type}"
        visitor = getattr(self, method, self.generic_visit)
        visitor(node)
    
    def generic_visit(self, node):
        for child in node.children:
            self.visit(child)

    def visit_loop(self, node):
        self.depth += 1
        self.generic_visit(node)
        self.depth -= 1

    def visit_function_def(self, node):
        original_depth = self.depth
        self.depth = 0
        self.generic_visit(node)
        self.depth = original_depth

    def visit_global_statment(self, node):
        for child in node.children:
            if hasattr(child, 'node_type') and child.node_type == "identifier":
                self.global_vars.add(child.metadata.get("name", ""))
        self.generic_visit(node)