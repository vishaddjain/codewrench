from .base import BaseDetectors

class LanguageDetectors(BaseDetectors):

    CPP_LARGE_TYPES = {"vector", "string", "map", "set", "unordered_map", "array", "deque", "list"}

    def __init__(self, language):
        super().__init__(language)

    def visit_loop(self, node):
        name = node.metadata.get("loop_type", None)
        if self.language == "javascript":
            if name == "for_in_statement":
                self.warnings.append(
                    f"'for...in' used on array at line {node.lineno} — 'for...in' is for objects, use 'for...of' or '.forEach()' instead."
                )
        super().visit_loop(node)

    def visit_goroutine(self, node):
        if self.depth >= 1:
            self.warnings.append(
                f"Goroutine spawned inside loop at line {node.lineno} — risk of unbounded goroutine creation, use a worker pool instead."
            )
        self.generic_visit(node)
    
    def visit_function_def(self, node):
        params = node.metadata.get("params", [])
        if self.language == "cpp":
           for param in params:
                has_large_type = any(t in param for t in self.CPP_LARGE_TYPES)
                has_reference = "&" in param
                if has_large_type and not has_reference:
                    self.warnings.append(
                        f"Pass by value at line {node.lineno} — '{param}' is a large type, use const reference instead (const {param}& name)."
                    )
        super().visit_function_def(node)
