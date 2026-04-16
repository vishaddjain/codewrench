from .base import BaseDetectors

class HighDetectors(BaseDetectors):
    
    CHEAP_CALLS = {
        "print", "len", "range", "str", "int", "float", "bool", "type",
        "append", "pop", "keys", "items", "values", "extend", "update",
        "get", "add", "remove", "copy", "clear", "discard", "isinstance",
        "getattr", "setattr", "hasattr", "iter", "next", 
        "reversed", "enumerate", "zip", "map", "filter", "any", "all",
        "repr", "hash", "id", "callable", "vars", "dir"
    }   
    ORM_CALLS = {
    # Django
    "filter", "first", "last", "exclude", "aggregate", "annotate",
    # SQLAlchemy  
    "query", "execute", "fetchall", "fetchone", "scalar",
    # General
    "find", "find_one", "find_many", "select", "insert", "delete"
    }
    EXPENSIVE_CALLS = {"open", "requests.get", "requests.post", "requests.put", "requests.delete", "requests.patch"}
    EXPENSIVE_SUFFIXES = {"read", "write", "connect", "execute", "fetchall", "fetchone"}
    UNNECESSARY_OBJECT = {"dict", "list", "tuple", "set", "object"}
    COUNTER_NAMES = {"i", "j", "k", "n", "x", "y", "z", "count", "counter", "index", "total", "num", "idx", "cnt"}
    ATTR_SKIP_PREFIXES = ("self.assert", "assert", "self.subTest")
    ATTR_SKIP_EXACT = {
        "assert", "date", "pk", "id", "count", "order_by", "get", "filter",
        "aggregate", "annotate", "create", "widget", "join"
    }
    REPORTING_FUNCTION_HINTS = {
        "print", "print_summary", "print_profiling", "save_report",
        "analyse_single_file", "analyse_folder"
    }

    def __init__(self, language, context):
        super().__init__(language, context)

    def visit_loop(self, node):
        self.depth += 1
        if self.depth >= 2 :
            self.warnings.append({
                "message": f"Nested loop at line {node.lineno} - potential O(n²).",
                "line": node.lineno,
                "confidence": "high",
                "function": self.current_function
            })
        self.generic_visit(node)
        self.depth -= 1
    
    def visit_function_call(self, node):
        name = node.metadata.get("name", None)
        if self.depth >= 1:
            if name and name == "re.compile":
                self.warnings.append({
                    "message": f"re.compile() inside loop at line {node.lineno} — move it outside the loop, compile once and reuse.",
                    "line": node.lineno,
                    "confidence": "high",
                    "function": self.current_function
                })
            elif name and name in ["print", "logging.info", "logging.warning", "logging.error", "console.log"]:
                if self.current_function in self.REPORTING_FUNCTION_HINTS:
                    self.generic_visit(node)
                    return
                self.warnings.append({
                    "message": f"print()/logging call inside loop at line {node.lineno} — I/O on every iteration, move outside or use buffered logging.",
                    "line": node.lineno,
                    "confidence": "medium",
                    "function": self.current_function
                })
            elif name and name == "len":
                self.warnings.append({
                    "message": f"len() called inside loop at line {node.lineno} — cache the result before the loop to avoid repeated calls.",
                    "line": node.lineno,
                    "confidence": "high",
                    "function": self.current_function
                })
            elif name and (name in self.EXPENSIVE_CALLS or name.split(".")[-1] in self.EXPENSIVE_SUFFIXES):
                self.warnings.append({
                    "message": f"I/O call {name} inside loop at line {node.lineno} - consider moving/removing it out.",
                    "line": node.lineno,
                    "confidence": "high",
                    "function": self.current_function
                })
            elif name and name in self.UNNECESSARY_OBJECT:
                self.warnings.append({
                    "message": f"Creating new object/literal inside loop - causes GC/allocation pressure. Consider moving outside or reusing.",
                    "line": node.lineno,
                    "confidence": "medium",
                    "function": self.current_function
                })
            elif name and name.split(".")[-1] in self.ORM_CALLS:
                self.warnings.append({
                    "message": f"Potential N+1 query — '{name}' called inside loop at line {node.lineno} — consider batching queries or using select_related/prefetch_related.",
                    "line": node.lineno,
                    "confidence": "medium",
                    "function": self.current_function
                })
        if name and name not in self.CHEAP_CALLS and name.split(".")[-1] not in self.CHEAP_CALLS:
            if self.depth >= 1:
                self.warnings.append({
                    "message": f"Function call '{name}' inside loop at line {node.lineno} — consider moving it out.",
                    "line": node.lineno,
                    "confidence": "low",
                    "function": self.current_function
                })

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
        var_name = node.metadata.get("var_name", "")
        join_hint = "''.join()" if self.language == "python" else "array.join('')"
        if var_name in self.COUNTER_NAMES:
            self.generic_visit(node)
            return
        if self.depth >= 2:
            self.warnings.append({
                "message": f"String concatenation in nested loop — quadratic complexity at line {node.lineno}, use {join_hint} outside the loop",
                "line": node.lineno,
                "confidence": "high",
                "function": self.current_function
            })
        elif self.depth >= 1:
            self.warnings.append({
                "message": f"String concatenation at line {node.lineno} — use {join_hint} instead.",
                "line": node.lineno,
                "confidence": "high",
                "function": self.current_function
            })
        self.generic_visit(node)

    def check_attr_counts(self):
        for key, lines in self.attr_counts.items():
            unique_lines = sorted(set(lines))
            if self.should_skip_attr_warning(key):
                continue

            threshold = 5 if self.context.is_test_file else 3
            if len(unique_lines) >= threshold:
                self.warnings.append({
                    "message": f"Attribute '{key}' accessed {len(unique_lines)} times in loop at lines {unique_lines} — cache it.",
                    "line": unique_lines[0],
                    "confidence": "high",
                    "function": self.current_function
                })

    def should_skip_attr_warning(self, key):
        if not key:
            return True

        if key.startswith(self.ATTR_SKIP_PREFIXES):
            return True

        if key in self.ATTR_SKIP_EXACT:
            return True

        last_part = key.split(".")[-1]
        if last_part in self.ATTR_SKIP_EXACT:
            return True

        if self.context.is_test_file and (
            key.endswith(".objects") or
            key.startswith("self.") or
            ".objects." in key
        ):
            return True

        return False

    def visit_await(self, node):
        if self.depth >= 1:
            self.warnings.append({
                "message" : f"await inside loop at line {node.lineno} — sequential async calls, use asyncio.gather() or Promise.all() to run concurrently.",
                "line": node.lineno,
                "confidence": "high",
                "function": self.current_function
            })
