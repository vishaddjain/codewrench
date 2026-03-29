from .base import BaseDetectors

class HighDetectors(BaseDetectors):
    
    CHEAP_CALLS = {"print", "len", "range", "str", "int", "float", "bool", "type"}
    EXPENSIVE_CALLS = {"open", "requests", "get", "post", "read", "write", "connect", "execute"}
    UNNECESSARY_OBJECT = {"dict", "list", "tuple", "set", "object"}

    def visit_loop(self, node):
        self.depth += 1
        if self.depth >= 2 :
            self.warnings.append(
                f"Nested loop at line {node.lineno} - potential O(n²)."
            )
        self.generic_visit(node)
        self.depth -= 1
    
    def visit_function_call(self, node):
        if self.depth >= 1:
            name = node.metadata.get("name", None)
            if name and name == "re.compile":
                self.warnings.append(
                    f"re.compile() inside loop at line {node.lineno} — move it outside the loop, compile once and reuse."
                )
            elif name and name in ["print", "logging.info", "logging.warning", "logging.error"]:
                self.warnings.append(
                    f"print()/logging call inside loop at line {node.lineno} — I/O on every iteration, move outside or use buffered logging."
                )
            elif name and name == "len":
                self.warnings.append(
                    f"len() called inside loop at line {node.lineno} — cache the result before the loop to avoid repeated calls."
                )
            elif name and name in self.EXPENSIVE_CALLS:
                self.warnings.append(
                    f"I/O call {name} inside loop at line {node.lineno} - consider moving/removing it out."
                )
            elif name and name in self.UNNECESSARY_OBJECT:
                self.warnings.append(
                    f"Creating new object/literal inside loop - causes GC/allocation pressure. Consider moving outside or reusing."
                )
            elif name and name not in self.CHEAP_CALLS:
                self.warnings.append(
                    f"Function call '{name}' inside loop at line {node.lineno} — consider moving it out."
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
        if self.depth >= 2:
            self.warnings.append(
                f"String concatenation in nested loop — quadratic complexity at line {node.lineno}, use join() outside the loop"
            )
        elif self.depth >= 1:
            self.warnings.append(
                f"String concatenation at line {node.lineno} — use ''.join() instead."
            )
        self.generic_visit(node)

    def check_attr_counts(self):
        for key, lines in self.attr_counts.items():
            if len(lines) >= 2:
                self.warnings.append(
                    f"Attribute '{key}' accessed {len(lines)} times in loop at lines {lines} — cache it."
                )
    def visit_await(self, node):
        if self.depth >= 1:
            self.warnings.append(
                f"await inside loop at line {node.lineno} — sequential async calls, use asyncio.gather() or Promise.all() to run concurrently."
            )