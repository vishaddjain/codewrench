from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
import tree_sitter_typescript as tstypescript
import tree_sitter_go as tsgo
import tree_sitter_c as tsc
import tree_sitter_cpp as tscpp

LANGUAGES = {
    "python": Language(tspython.language()),
    "javascript": Language(tsjavascript.language()),
    "typescript": Language(tstypescript.language_typescript()),
    "go": Language(tsgo.language()),
    "c": Language(tsc.language()),
    "cpp": Language(tscpp.language()),
}

def get_parser(language) :
    parser = Parser(LANGUAGES[language])
    return parser

def detect_language(filename):
    ext = filename.split(".")[-1]
    mapping = {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "go": "go",
        "c": "c",
        "cpp": "cpp",
        "cc": "cpp",
    }
    return mapping.get(ext, None)

