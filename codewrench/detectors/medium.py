from .base import BaseDetectors

class MediumDetectors(BaseDetectors):

    SORT_CALLS = {"sort", "sorted", "sort_by", "order_by"}
    COUNTER_NAMES = {"i", "j", "k", "n", "x", "y", "z", "count", "index", "total", "num", "idx", "cnt"}
    LINEAR_SEARCH_CALLS = {"index", "count"}

    def __init__(self, language, context):
        super().__init__(language, context)

    def visit_global_statement(self, node):
        names = node.metadata.get("names", [])
        for name in names:
            self.global_vars.add(name)
        self.generic_visit(node)

    def visit_function_call(self, node):

        name = node.metadata.get("name", None)

        if self.depth >= 1:
            if name and name in self.SORT_CALLS:
                self.warnings.append({
                    "message": f"Unnecessary sorting {name} inside loops at line {node.lineno}.",
                    "line": node.lineno,
                    "confidence": "medium",
                    "function": self.current_function
                }) 
            elif name and name.split(".")[-1] in self.LINEAR_SEARCH_CALLS:
                self.warnings.append({
                    "message": f"Linear search — '{name}' called inside loop at line {node.lineno} — list.index() and .count() are O(n), use a dict or set for O(1) lookups.",
                    "line": node.lineno,
                    "confidence": "high",
                    "function": self.current_function
                })

        if self.depth >= 2:
            if name == "append":
                self.warnings.append({
                    "message": f"List append inside nested loop at line {node.lineno} — consider restructuring.",
                    "line": node.lineno,
                    "confidence": "medium",
                    "function": self.current_function
                })
                
        if name == "list":
            children_names = [
                c.metadata.get("name", "") 
                for c in node.children
            ]
            if "range" in children_names:
                self.warnings.append({
                    "message": f"Unnecessary list creation at line {node.lineno} — just use range(n) directly.",
                    "line": node.lineno,
                    "confidence": "high",
                    "function": self.current_function
                })
        
        self.generic_visit(node)

    def visit_exception_handler(self, node):
        exception_type = node.metadata.get("exception_type", None)
        if exception_type is None:
            self.warnings.append({
                "message": f"Bare except at line {node.lineno} — catches everything, be specific.",
                "line": node.lineno,
                "confidence": "high",
                "function": self.current_function
            })
        elif exception_type == "Exception":
            self.warnings.append({
                "message": f"Overly broad 'except Exception' at line {node.lineno} — catch specific exceptions.",
                "line": node.lineno,
                "confidence": "medium",
                "function": self.current_function
            })
        if self.depth >= 1:
            self.warnings.append({
                "message": f"try/except inside loop at line {node.lineno} — exception handling overhead on every iteration, move outside if possible.",
                "line": node.lineno,
                "confidence": "low",
                "function": self.current_function
            })
        self.generic_visit(node)

    def visit_function_def(self, node):
        defaults = node.metadata.get("mutable_defaults", [])
        for lineno in defaults:
            self.warnings.append({
                "message": f"Mutable default argument at line {lineno} — use None instead.",
                "line": lineno,
                "confidence": "high",
                "function": self.current_function
            })
        super().visit_function_def(node)


    def visit_identifier(self, node):
        if self.depth >= 1:
            name = node.metadata.get("name", None)
            if name and name in self.global_vars:
                self.warnings.append({
                    "message": f"Global variable '{name}' accessed inside loop at line {node.lineno} — consider caching it locally.",
                    "line": node.lineno,
                    "confidence": "medium",
                    "function": self.current_function
                })
        self.generic_visit(node)

    def visit_import(self, node):
        if self.function_depth >= 1:
            self.warnings.append({
                "message": f"Import is at function level instead of top at line {node.lineno}.",
                "line": node.lineno,
                "confidence": "high",
                "function": self.current_function
            })
        self.generic_visit(node)

    def visit_list_concat(self, node):
        if self.depth >= 1:
            var_name = node.metadata.get("var_name", "")
            if var_name in self.COUNTER_NAMES:
                self.generic_visit(node)
                return
            self.warnings.append({
                "message": f"List concatenation with '+' inside loop at line {node.lineno} — use .extend() or += instead, avoids creating a new list each iteration.",
                "line": node.lineno,
                "confidence": "high",
                "function": self.current_function
            })
        self.generic_visit(node)