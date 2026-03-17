import ast
from .base import BaseDetectors

class MediumDetectors(ast.NodeVisitor):

    def visit_Call(self, node):
        if self.depth >= 2:
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == "append":
                    self.warnings.append(
                        f"List append inside nested loop at line {node.lineno} — consider restructuring"
                    )
        self.generic_visit(node)

    def visit_Name(self, node):
        if self.depth >= 1 and node.id in self.global_vars:
            access_type = "Accessed" if isinstance(node.ctx, ast.Load) else "modified"
            self.warnings.append(
                f"Global variable '{node.id}' {access_type} inside loop at line {node.lineno} — consider caching it locally"
            )
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        if node.type is None:
            self.warnings.append(
                f"Bare except at line {node.lineno} — catches everything including system exceptions, be specific"
            )
        elif isinstance(node.type, ast.name) and node.type.id == "Exception":
            self.warnings.append(
                f"Overly broad 'except Exception' at line {node.lineno} — consider catching a specific exception"
            )
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id == "list":
               if len(node.args) > 0:
                   first_arg = node.args[0]
                   if isinstance(first_arg, ast.Call):
                       if isinstance(first_arg.func, ast.Name):
                            if first_arg.func.id =="range":
                                self.warnings.append(
                                f"Unnecessary list creation at line {node.lineno} — list(range(n)) wastes memory, just use range(n) directly"
                            )
        self.generic_visit(node)