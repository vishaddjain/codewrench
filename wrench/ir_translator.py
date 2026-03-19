from ir import IRNode

GENERIC_TYPES = {
    "LOOP": "loop",
    "FUNCTION_CALL": "function_call",
    "FUNCTION_DEF": "function_def",
    "ATTRIBUTE_ACCESS": "attribute_access",
    "STRING_CONCAT": "string_concat",
    "EXCEPTION_HANDLER": "exception_handler",
    "GLOBAL_STATEMENT": "global_statement",
}

class IRTranslator:
    def __init__(self, rules):
        self.rules = rules

    def translate(self, node):
        node_type = self.get_generic_type(node.type)
        lineno = node.start_point[0] + 1
        children = [self.translate(child) for child in node.children]
        return IRNode(node_type or node.type, lineno, children)
    
    def extract_metadata(self, node, node_type):
        metadata = {}

        if node_type == "function_call":
            metadata["name"] = self.get_call_name(node)

        elif node_type == "attribute_access":
            metadata["name"] = self.get_attribute_name(node)
        
        elif node_type == "identifier":
            metadata["name"] = node.text.decode("utf8") if node.text else None
        
        elif node_type == "exception_handler":
                metadata["exception_type"] = self.get_exception_type(node)

        elif node_type == "function_def":
            metadata["mutable_defaults"] = self.get_mutable_defaults(node)

        elif node_type == "global_statement":
            metadata["names"] = [
                child.text.decode("utf8") 
                for child in node.children 
                if child.type == "identifier"
            ]

        return metadata

    def get_call_name(self, node):
        for child in node.children:
            if child.type == "identifier":
                return child.text.decode("utf8")
            elif child.type == "attribute":
                for subchild in child.children:
                    if subchild.type == "identifier":
                        return subchild.text.decode("utf8")
        return None

    def get_attribute_name(self, node):
        parts = []
        for child in node.children:
            if child.type == "identifier":
                parts.append(child.text.decode("utf8"))
        return ".".join(parts) if parts else None

    def get_exception_type(self, node):
        for child in node.children:
            if child.type == "identifier":
                return child.text.decode("utf8")
        return None

    def get_mutable_defaults(self, node):
        mutable_lines = []
        for child in node.children:
            if child.type in ("list", "dictionary", "set"):
                mutable_lines.append(child.start_point[0] + 1)
        return mutable_lines

    def get_generic_type(self, tree_sitter_type):
        for generic, mapped in GENERIC_TYPES.items():
            rule_list = getattr(self.rules, generic + "_TYPES",
                          getattr(self.rules, generic, []))
            if tree_sitter_type in rule_list:
                return mapped
        return None