import ast 

class BaseDetectors(ast.NodeVisitor):
    def __init__(self):
        self.depth = 0
        self.warnings = []
        self.attr_counts = {}
        self.global_vars = set()

    def visit_For(self, node):
        self.depth += 1
        if self.depth >= 2 :
            self.warnings.append(
                f"Nested loop at line {node.lineno} - potential O(n²)"
            )
        self.generic_visit(node)
        self.depth -= 1

    visit_While = visit_For

    def visit_FunctionDef(self, node):
        original_depth = self.depth
        self.depth = 0
        self.generic_visit(node)
        self.depth = original_depth

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Global(self, node):
        for name in node.names:
            self.global_vars.add(name)
        self.generic_visit(node)