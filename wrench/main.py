import sys
import os
import threading
from detectors.high import HighDetectors
from detectors.medium import MediumDetectors
from ai_engine import analyse, get_fixed_code, analyse_folder as analyse_folder_ai
from parser_engine import get_parser, detect_language
from ir_translator import IRTranslator
from profilers.profiler import profile_file, parse_stats, write_temp_file, delete_temp_file
from errors import handle_error
from wrenchignore import load_wrenchignore, is_ignored
from reports import print_summary, print_profiling, ask_and_analyse, ask_and_apply_fixes, save_report

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
    # wrenchignore check
    patterns = load_wrenchignore(os.path.dirname(filepath))
    if is_ignored(filepath, patterns):
        return [], None, None

    # language check
    language = detect_language(filepath)
    if language is None:
        handle_error("unsupported_language", filepath)
        return [], None, None

    # file reading
    try:
        with open(filepath, "r", encoding="utf8") as f:
            code = f.read()
    except FileNotFoundError:
        handle_error("file_not_found", filepath, fatal=True)
    except PermissionError:
        handle_error("permission_error", filepath)
        return [], None, None
    except UnicodeDecodeError:
        handle_error("binary_file", filepath)
        return [], None, None

    # empty file check
    if not code.strip():
        handle_error("empty_file", filepath)
        return [], None, None

    # parsing
    try:
        rules = get_rules(language)
        parser = get_parser(language)
        tree = parser.parse(bytes(code, "utf8"))
        translator = IRTranslator(rules)
        ir_tree = translator.translate(tree.root_node)
    except Exception:
        handle_error("syntax_error", filepath)
        return [], None, None

    warnings = []
    for DetectorClass in [HighDetectors, MediumDetectors]:
        detector = DetectorClass()
        detector.visit(ir_tree)
        if hasattr(detector, 'check_attr_counts'):
            detector.check_attr_counts()
        warnings.extend(detector.warnings)

    return warnings, language, code

def get_files(folder):
    patterns = load_wrenchignore(folder)
    files = []
    for root, dirs, filenames in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in filenames:
            filepath = os.path.join(root, f)
            if detect_language(f) is not None and not is_ignored(filepath, patterns):
                files.append(filepath)
    return files

def analyse_single_file(filename):
    warnings, language, code = run_analysis(filename)

    if language is None:
        return

    if not warnings:
        print("No issues found!")
        return

    # print summary
    print_summary(1, {language}, {filename: warnings})

    # print warnings
    print("\n--- Warnings ---\n")
    for w in warnings:
        print(f"  {w}")

    results = {}

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

        except Exception:
            handle_error("profiling_error", filename)
            results["profiling"] = None

    t = threading.Thread(target=run_profiling)
    t.start()
    t.join()

    # profiling output
    if results.get("profiling") is None and language != "python":
        print("\n--- Profiling not supported for this language yet ---")
    elif results.get("before") and results.get("after"):
        print_profiling(results["before"], results["after"])

    # AI analysis — ask user
    ask_and_analyse(code, warnings)

    # apply fixes — ask user
    ask_and_apply_fixes(code, warnings, filename)

    # save report — ask user
    save_report(1, {language}, {filename: warnings})

def analyse_folder(folder):
    files = get_files(folder)

    if not files:
        print("No supported files found in folder.")
        return

    all_results = {}
    languages = set()
    for file in files:
        warnings, language, code = run_analysis(file)
        if language:
            languages.add(language)
        if warnings:
            all_results[file] = warnings

    if not all_results:
        print("No issues found across all files!")
        return

    # print summary
    print_summary(len(files), languages, all_results)

    # print warnings per file
    print("\n--- Warnings ---\n")
    for file, warnings in all_results.items():
        print(f"--- {file} ---")
        for w in warnings:
            print(f"  {w}")
        print()

    # AI analysis — one call for whole folder, ask user
    analysis = None
    choice = input("\nWant AI analysis? (y/n): ").strip().lower()
    if choice == 'y':
        try:
            analysis = analyse_folder_ai(all_results)
            print("\n--- AI Analysis ---\n")
            print(analysis)
        except Exception:
            handle_error("api_error", folder)

    # save report — ask user
    save_report(len(files), languages, all_results, analysis=analysis)

if len(sys.argv) < 2:
    print("Usage: python main.py <filename or folder>")
    exit()

target = sys.argv[1]

if os.path.isdir(target):
    analyse_folder(target)
elif os.path.isfile(target):
    analyse_single_file(target)
else:
    handle_error("file_not_found", target, fatal=True)