import ast
import sys
import os
from detectors.high import HighDetectors
from detectors.medium import MediumDetectors
from ai_engine import analyse
from parser_engine import get_parser, detect_language
from ir_translator import IRTranslator

if len(sys.argv) < 2:
    print("Usage: python main.py <filename>")
    exit()

filename = sys.argv[1]

if not os.path.exists(filename):
    print(f"Error: file '{filename}' not found")
    exit()

language = detect_language(filename)
if language is None:
    print(f"Unsupported file type: {filename}")
    exit()

code = open(filename).read()

if language == "python":
    import languages.python_rules as rules
elif language == "javascript":
    import languages.javascript_rules as rules
elif language == "typescript":
    import languages.typescript_rules as rules
elif language == "go":
    import languages.go_rules as rules
elif language == "c":
    import languages.c_rules as rules
elif language == "cpp":
    import languages.cpp_rules as rules

parser = get_parser(language)
tree = parser.parse(bytes(code, "utf8"))
translator = IRTranslator(rules)
ir_tree = translator.translate(tree.root_node)

all_warnings = []

for DetectorClass in [HighDetectors, MediumDetectors]:
    detector = DetectorClass()
    detector.visit(ir_tree)
    if hasattr(detector, 'check_attr_counts'):
        detector.check_attr_counts()
    all_warnings.extend(detector.warnings)

if all_warnings:
    for w in all_warnings:
        print(w)
else:
    print("No issues found!")

result = analyse(code, all_warnings)
print("\n--- AI Analysis ---\n")
print(result)