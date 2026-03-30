from .base import BaseDetectors

class MediumDetectors(BaseDetectors):

    SORT_CALLS = {"sort", "sorted", "sort_by", "order_by"}

    def __init__(self):
        super().__init__()

    def visit_global_statement(self, node):
        names = node.metadata.get("names", [])
        for name in names:
            self.global_vars.add(name)
        self.generic_visit(node)

    def visit_function_call(self, node):

        name = node.metadata.get("name", None)

        if self.depth >= 1:
            if name and name in self.SORT_CALLS:
                self.warnings.append(
                    f"Unnecessary sorting {name} inside loops at line {node.lineno}."
                ) 

        if self.depth >= 2:
            if name == "append":
                self.warnings.append(
                    f"List append inside nested loop at line {node.lineno} — consider restructuring."
                )

        if name == "list":
            children_names = [
                c.metadata.get("name", "") 
                for c in node.children
            ]
            if "range" in children_names:
                self.warnings.append(
                    f"Unnecessary list creation at line {node.lineno} — just use range(n) directly."
                )
        
        self.generic_visit(node)

    def visit_exception_handler(self, node):
        exception_type = node.metadata.get("exception_type", None)
        if exception_type is None:
            self.warnings.append(
                f"Bare except at line {node.lineno} — catches everything, be specific."
            )
        elif exception_type == "Exception":
            self.warnings.append(
                f"Overly broad 'except Exception' at line {node.lineno} — catch specific exceptions."
            )
        if self.depth >= 1:
            self.warnings.append(
                f"try/except inside loop at line {node.lineno} — exception handling overhead on every iteration, move outside if possible."
            )
        self.generic_visit(node)

    def visit_function_def(self, node):
        defaults = node.metadata.get("mutable_defaults", [])
        for lineno in defaults:
            self.warnings.append(
                f"Mutable default argument at line {lineno} — use None instead."
            )
        super().visit_function_def(node)


    def visit_identifier(self, node):
        if self.depth >= 1:
            name = node.metadata.get("name", None)
            if name and name in self.global_vars:
                self.warnings.append(
                    f"Global variable '{name}' accessed inside loop at line {node.lineno} — consider caching it locally."
                )
        self.generic_visit(node)

    def visit_import(self, node):
        if self.function_depth >= 1:
            self.warnings.append(
                f"Import is at function level instead of top at line {node.lineno}."
            )
        self.generic_visit(node)

    def visit_list_concat(self, node):
        if self.depth >= 1:
            self.warnings.append(
                f"List concatenation with '+' inside loop at line {node.lineno} — use .extend() or += instead, avoids creating a new list each iteration."
            )
        self.generic_visit(node)