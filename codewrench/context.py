import os

class ContextAnalyser:

    COLD_PATH_NAMES = {"setup", "init", "configure", "load", "parse",
                       "bootstrap", "initialise", "initialize", "migrate"}

    HOT_PATH_NAMES = {"handle", "process", "request", "render",
                      "compute", "run", "execute", "dispatch", "update"}

    def __init__(self, filename):
        self.filename = filename
        self.normalized_path = os.path.normpath(self.filename).lower()
        self.path_parts = self.normalized_path.split(os.sep)
        self.is_test_file = self._check_test_file()
        self.is_script_file = self._check_script_file()
        self.is_tutorial_file = self._check_tutorial_file()
        self.function_contexts = {}
        self._call_counts = {}

    def _check_test_file(self):
        if "tests" in self.path_parts or "js_tests" in self.path_parts or "__tests__" in self.path_parts:
            return True

        base = os.path.basename(self.normalized_path)
        name, ext = os.path.splitext(base)
        return (
            name.startswith("test_") or
            name.endswith("_test") or
            ".test." in base or
            ".spec." in base or
            "spec" in name
        )

    def _check_script_file(self):
        return "scripts" in self.path_parts or "script" in self.path_parts

    def _check_tutorial_file(self):
        tutorial_dirs = {"docs", "docs_src", "examples", "example", "tutorial", "tutorials"}
        return any(part in tutorial_dirs for part in self.path_parts)
    
    def _walk(self, node, visitor):
        visitor(node)
        for child in node.children:
            self._walk(child, visitor)

    def _register_functions(self, node):
        if node.node_type == "function_def":
            name = node.metadata.get("name", None)
            if name:
                is_cold = any(hint in name.lower() for hint in self.COLD_PATH_NAMES)
                is_hot = any(hint in name.lower() for hint in self.HOT_PATH_NAMES)
                self.function_contexts[name] = {
                    "is_cold" : is_cold,
                    "is_hot" : is_hot,
                    "call_count": 0
                }

    def _count_calls(self, node):
        if node.node_type == "function_call":
            name = node.metadata.get("name", None)
            if name:
                base_name = name.split(".")[-1]
                if base_name in self.function_contexts:
                    self.function_contexts[base_name]["call_count"] += 1

    def analyse(self, ir_tree):
        self._walk(ir_tree, self._register_functions)
        self._walk(ir_tree, self._count_calls)

    def get_context(self, function_name):
        if function_name is None:
            return {"is_cold": False, "is_hot": False, "call_count": -1}
        return self.function_contexts.get(function_name, {
            "is_cold": False, "is_hot": False, "call_count": -1
        })    
