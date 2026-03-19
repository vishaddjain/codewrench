from .base import BaseDetectors

class MediumDetectors(BaseDetectors):

    def __init__(self):
        super().__init__()

    def visit_function_call(self, node):
        if self.depth >= 2:
            name = node.metadata.get("name", None)
            if name == "append":
                self.warnings.append(
                    f"List append inside nested loop at line {node.lineno} — consider restructuring"
                )

        name = node.metadata.get("name", None)
        if name == "list":
            children_names = [
                c.metadata.get("name", "") 
                for c in node.children
            ]
            if "range" in children_names:
                self.warnings.append(
                    f"Unnecessary list creation at line {node.lineno} — just use range(n) directly"
                )

        self.generic_visit(node)

    def visit_exception_handler(self, node):
        exception_type = node.metadata.get("exception_type", None)
        if exception_type is None:
            self.warnings.append(
                f"Bare except at line {node.lineno} — catches everything, be specific"
            )
        elif exception_type == "Exception":
            self.warnings.append(
                f"Overly broad 'except Exception' at line {node.lineno} — catch specific exceptions"
            )
        self.generic_visit(node)

    def visit_function_def(self, node):
        defaults = node.metadata.get("mutable_defaults", [])
        for lineno in defaults:
            self.warnings.append(
                f"Mutable default argument at line {lineno} — use None instead"
            )
        super().visit_function_def(node)

    def visit_identifier(self, node):
        if self.depth >= 1:
            name = node.metadata.get("name", None)
            if name and name in self.global_vars:
                self.warnings.append(
                    f"Global variable '{name}' accessed inside loop at line {node.lineno} — consider caching it locally"
                )
        self.generic_visit(node)

            