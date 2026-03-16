import ast

class NestedLoopDetector(ast.NodeVisitor):
    
    CHEAP_CALLS = {"print", "len", "range", "str", "int", "float", "bool", "type"}

    def __init__(self):
        self.depth = 0
        self.warnings = []
        self.attr_counts = {}

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

    def visit_Call(self, node):
        if self.depth >= 1:
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            else:
                name = None
            
            if name and name not in self.CHEAP_CALLS:
                self.warnings.append(
                    f"Function call '{name}' inside loop at line {node.lineno} — consider moving it out"
                )

        self.generic_visit(node)

    def visit_Attribute(self, node):
        if self.depth >= 1:
            if isinstance(node.value, node.Name):
                obj_name = node.value.id
                attr_name = node.attr
                key = f"{obj_name}.{attr_name}"

                if key not in self.attr_counts:
                    self.attr_counts[key] = []
                self.attr_counts[key].append(node.lineno)

        self.generic_visit(node)
    
    def check_attr_counts(self):
        for key, lines in self.attr_counts.items():
            if len(lines) >= 2:
                self.warnings.append(
                    f"Attribute '{key}' accessed {len(lines)} times in a loop at lines {lines} — cache it before the loop"
                )

    def visit_AugAssign(self, node):
        if self.depth >= 1:
            if isinstance(node.op, ast.Add):
                self.warnings.append(
                    f"String concatenation with += at line {node.lineno} — use ''.join() instead"
                )
        self.generic_visit(node)

# tree = ast.parse(code)
# detector = NestedLoopDetector()
# detector.visit(tree)

# if detector.warnings:
#     for w in detector.warnings:
#         print(w)
# else:
#     print("No issues found!")