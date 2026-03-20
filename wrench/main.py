import sys
import os
import threading
from detectors.high import HighDetectors
from detectors.medium import MediumDetectors
from ai_engine import analyse, get_fixed_code
from parser_engine import get_parser, detect_language
from ir_translator import IRTranslator
from profilers.profiler import profile_file, parse_stats, write_temp_file, delete_temp_file

IGNORE_DIRS = {"venv", "node_modules", ".git", "__pycache__", "dist", "build", ".vscode"}

def get_rules(language):
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
    else:
        return None
    return rules

def run_analysis(filepath):
    language = detect_language(filepath)
    if language is None:
        return [], language, None

    code = open(filepath).read()
    rules = get_rules(language)

    parser = get_parser(language)
    tree = parser.parse(bytes(code, "utf8"))
    translator = IRTranslator(rules)
    ir_tree = translator.translate(tree.root_node)

    warnings = []
    for DetectorClass in [HighDetectors, MediumDetectors]:
        detector = DetectorClass()
        detector.visit(ir_tree)
        if hasattr(detector, 'check_attr_counts'):
            detector.check_attr_counts()
        warnings.extend(detector.warnings)

    return warnings, language, code

def get_files(folder):
    files = []
    for root, dirs, filenames in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in filenames:
            if detect_language(f) is not None:
                files.append(os.path.join(root, f))
    return files

def analyse_single_file(filename):
    warnings, language, code = run_analysis(filename)

    if not warnings:
        print("No issues found!")
        return

    for w in warnings:
        print(w)

    results = {}

    def run_explanation():
        results["explanation"] = analyse(code, warnings)

    def run_profiling():
        try:
            if language != "python":
                results["profiling"] = None
                return

            before_raw = profile_file(filename)
            before_stats = parse_stats(before_raw)

            fixed_code = get_fixed_code(code, warnings)
            temp_file = write_temp_file(fixed_code, filename)
            after_raw = profile_file(temp_file)
            after_stats = parse_stats(after_raw)
            delete_temp_file(temp_file)

            results["before"] = before_stats
            results["after"] = after_stats

        except Exception as e:
            print(f"Profiling error: {e}")
            results["profiling"] = None

    t1 = threading.Thread(target=run_explanation)
    t2 = threading.Thread(target=run_profiling)

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print("\n--- AI Analysis ---\n")
    print(results["explanation"])

    if results.get("profiling") is None and language != "python":
        print("\n--- Profiling not supported for this language yet ---")
    elif results.get("before") and results.get("after"):
        print("\n--- Performance Profile ---\n")
        print("Top 5 slowest functions BEFORE fix:")
        for stat in results["before"][:5]:
            func = stat['function'].split(":")[-1]
            print(f"  {func:<30} cumtime: {stat['cumtime']}s")

        print("\nTop 5 slowest functions AFTER fix:")
        for stat in results["after"][:5]:
            func = stat['function'].split(":")[-1]
            print(f"  {func:<30} cumtime: {stat['cumtime']}s")

def analyse_folder(folder):
    files = get_files(folder)

    if not files:
        print("No supported files found in folder.")
        return

    print(f"Found {len(files)} files to analyse...\n")

    all_results = {}
    for file in files:
        warnings, language, code = run_analysis(file)
        if warnings:
            all_results[file] = warnings

    if not all_results:
        print("No issues found across all files!")
        return

    total = sum(len(w) for w in all_results.values())
    print(f"Found {total} issues across {len(all_results)} files:\n")

    for file, warnings in all_results.items():
        print(f"--- {file} ---")
        for w in warnings:
            print(f"  {w}")
        print()

if len(sys.argv) < 2:
    print("Usage: python main.py <filename or folder>")
    exit()

target = sys.argv[1]

if os.path.isdir(target):
    analyse_folder(target)
elif os.path.isfile(target):
    analyse_single_file(target)
else:
    print(f"Error: '{target}' is not a valid file or folder")
    exit()