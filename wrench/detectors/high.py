from .base import BaseDetectors

class HighDetectors(BaseDetectors):
    
    CHEAP_CALLS = {"print", "len", "range", "str", "int", "float", "bool", "type"}

    def visit_loop(self, node):
        self.depth += 1
        if self.depth >= 2 :
            self.warnings.append(
                f"Nested loop at line {node.lineno} - potential O(n²)"
            )
        self.generic_visit(node)
        self.depth -= 1
    
    def visit_function_call(self, node):
        if self.depth >= 1:
            name = node.metadata.get("name", None)
            if name and name not in self.CHEAP_CALLS:
                self.warnings.append(
                    f"Function call '{name}' inside loop at line {node.lineno} — consider moving it out"
                )
        self.generic_visit(node)

    def visit_attribute_access(self, node):
        if self.depth >= 1:
            name = node.metadata.get("name", None)
            if name:
                if name not in self.attr_counts:
                    self.attr_counts[name] = []
                self.attr_counts[name].append(node.lineno)
        self.generic_visit(node)
    
    def visit_string_concat(self, node):
        if self.depth >= 1:
            self.warnings.append(
                f"String concatenation at line {node.lineno} — use ''.join() instead"
            )
        self.generic_visit(node)

    def check_attr_counts(self):
        for key, lines in self.attr_counts.items():
            if len(lines) >= 2:
                self.warnings.append(
                    f"Attribute '{key}' accessed {len(lines)} times in loop at lines {lines} — cache it"
                )
