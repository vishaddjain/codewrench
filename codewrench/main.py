import sys
import os
import threading
import argparse
from dotenv import load_dotenv
from .detectors.high import HighDetectors
from .detectors.medium import MediumDetectors
from .detectors.lang_detectors import LanguageDetectors
from .ai_engine import analyse, get_fixed_code, analyse_folder as analyse_folder_ai
from .parser_engine import get_parser, detect_language
from .ir_translator import IRTranslator
from .profilers.profiler import profile_file, profile_node, profile_go, parse_stats, write_temp_file, delete_temp_file
from .errors import handle_error
from .wrenchignore import load_wrenchignore, is_ignored
from .reports import print_summary, print_profiling, ask_and_analyse, ask_and_apply_fixes, save_report, revert_file
from .context import ContextAnalyser
from .confidence import filter_warnings

IGNORE_DIRS = {"venv", "node_modules", ".git", "__pycache__", "dist", "build", ".vscode"}

def get_rules(language):
    if language == "python":
        from .languages import python_rules as rules
    elif language == "javascript":
        from .languages import javascript_rules as rules
    elif language == "typescript":
        from .languages import typescript_rules as rules
    elif language == "go":
        from .languages import go_rules as rules
    elif language == "c":
        from .languages import c_rules as rules
    elif language == "cpp":
        from .languages import cpp_rules as rules
    else:
        return None
    return rules

def run_analysis(filepath, show_all=False):
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

    # wrench :ignore check
    def get_ignored_ranges(code, ir_tree):
        ignored_lines = set()
        for lineno, line in enumerate(code.splitlines(), start=1):
            if "wrench:ignore" in line:
                ignored_lines.add(lineno)
        
        ranges = []
        
        def walk(node):
            if node.node_type in ("loop", "function_def"):
                start = node.lineno
                end = node.metadata.get("end_lineno", start)
                if start in ignored_lines:
                    ranges.append((start, end))
            for child in node.children:
                walk(child)
        
        walk(ir_tree)
        
        for lineno in ignored_lines:
            if not any(start <= lineno <= end for start, end in ranges):
                ranges.append((lineno, lineno))
        
        return ranges

    # parsing
    try:
        rules = get_rules(language)
        parser = get_parser(language)
        tree = parser.parse(bytes(code, "utf8"))
        translator = IRTranslator(rules)
        ir_tree = translator.translate(tree.root_node)

        context = ContextAnalyser(filepath)
        context.analyse(ir_tree)

    except Exception:
        handle_error("syntax_error", filepath)
        return [], None, None

    warnings = []
    for DetectorClass in [HighDetectors, MediumDetectors, LanguageDetectors]:
        detector = DetectorClass(language, context)
        detector.visit(ir_tree)
        if hasattr(detector, 'check_attr_counts'):
            detector.check_attr_counts()
        warnings.extend(detector.warnings)
    
    ignored_ranges = get_ignored_ranges(code, ir_tree)
    warnings = [
        w for w in warnings
        if not any(start <= w["line"] <= end for start, end in ignored_ranges)
    ]
    warnings = filter_warnings(warnings, context, show_all=show_all)

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

def analyse_single_file(filename, args):
    warnings, language, code = run_analysis(filename, show_all=args.all)

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
        print(f"  {w['message']}")
    print()
    results = {}

    if args.profile:
        def run_profiling():
            if args.fix:
                try:
                    fixed_code = get_fixed_code(code, warnings)
                    temp_file = write_temp_file(fixed_code, filename)

                    if language == "python":
                        before_raw = profile_file(filename)
                        before_stats = parse_stats(before_raw)
                        after_raw = profile_file(temp_file)
                        after_stats = parse_stats(after_raw)
                        delete_temp_file(temp_file)
                        results["before"] = before_stats
                        results["after"] = after_stats
                        results["profiling_type"] = "cprofile"

                    elif language in ("javascript", "typescript"):
                        before_time = profile_node(filename)
                        after_time = profile_node(temp_file)
                        delete_temp_file(temp_file)
                        results["before_time"] = before_time
                        results["after_time"] = after_time
                        results["profiling_type"] = "time"

                    elif language == "go":
                        before_time = profile_go(filename)
                        after_time = profile_go(temp_file)
                        delete_temp_file(temp_file)
                        results["before_time"] = before_time
                        results["after_time"] = after_time
                        results["profiling_type"] = "time"

                    else:
                        results["profiling"] = None

                except Exception:
                    handle_error("profiling_error", filename)
                    results["profiling"] = None
            else:
                try:
                    if language == "python":
                        raw = profile_file(filename)
                        results["stats"] = parse_stats(raw)
                        results["profiling_type"] = "cprofile_single"

                    elif language in ("javascript", "typescript"):
                        time_taken = profile_node(filename)
                        results["single_time"] = time_taken
                        results["profiling_type"] = "time_single"

                    elif language == "go":
                        time_taken = profile_go(filename)
                        results["single_time"] = time_taken
                        results["profiling_type"] = "time_single"

                    else:
                        results["profiling"] = None

                except Exception:
                    handle_error("profiling_error", filename)
                    results["profiling"] = None
           
        t = threading.Thread(target=run_profiling)
        t.start()
        t.join()

        profiling_type = results.get("profiling_type")

        if profiling_type == "cprofile":
            print_profiling(results["before"], results["after"])
        elif profiling_type == "time":
            before = results["before_time"]
            after = results["after_time"]
            improvement = round((before - after) / before * 100, 1) if before > 0 else 0
            print("\n--- Performance Profile ---\n")
            print(f"  Execution time BEFORE fix: {before}s")
            print(f"  Execution time AFTER fix:  {after}s")
            print(f"  Improvement: {improvement}% faster")
        elif profiling_type == "cprofile_single":
            print_profiling(results["stats"], None)

        elif profiling_type == "time_single":
            print("\n--- Performance Profile ---\n")
            print(f"  Execution time: {results['single_time']}s")
        else:
            print("\n--- Profiling not supported for this language yet ---")

    # AI analysis — ask user
    if args.analyse:
        ask_and_analyse(code, warnings)

    # apply fixes — ask user
    if args.fix:
        ask_and_apply_fixes(code, warnings, filename, no_backup=args.no_backup)

    # save report — ask user
    if args.save_report:
        save_report(1, {language}, {filename: warnings})

def analyse_folder(folder, args):
    files = get_files(folder)

    if not files:
        print("No supported files found in folder.")
        return

    all_results = {}
    languages = set()
    for file in files:
        warnings, language, code = run_analysis(file, show_all=args.all)
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
            print(f"  {w['message']}")
        print()

    # AI analysis — one call for whole folder, ask user
    analysis = None
    if args.analyse:
        try:
            analysis = analyse_folder_ai(all_results)
            print("\n--- AI Analysis ---\n")
            print(analysis)
        except Exception:
            handle_error("api_error", folder)

    if args.fix:
        for file, file_warnings in all_results.items():
            _, _, file_code = run_analysis(file)
            ask_and_apply_fixes(file_code, file_warnings, file, no_backup=args.no_backup)
         
    # save report — ask user
    if args.save_report:
        save_report(len(files), languages, all_results, analysis=analysis)

def main():
    
    load_dotenv()

    parser = argparse.ArgumentParser(
        prog="codewrench",
        description="A multi-language code performance analyser."
    )
    parser.add_argument("target", nargs="?", help="File or folder to analyse")
    parser.add_argument("--revert", metavar="FILE", help="Revert AI fixes from .bak file")
    parser.add_argument("--analyse", action="store_true", help="Run AI analysis on detected issues")
    parser.add_argument("--fix", action="store_true", help="Apply AI fixes to files")
    parser.add_argument("--save-report", action="store_true", help="Save markdown report")
    parser.add_argument("--no-backup", action="store_true", help="Don't keep .bak backup when applying fixes")
    parser.add_argument("--profile", action="store_true", help="Run performance profiling on analysed files")
    parser.add_argument("--all", action="store_true", help="Show all warnings including low confidence")
        
    args = parser.parse_args()


    if args.revert:
        revert_file(args.revert)
    elif args.target:
        target = args.target
        if os.path.isdir(target):
            analyse_folder(target, args)
        elif os.path.isfile(target):
            analyse_single_file(target, args)
        else:
            handle_error("file_not_found", target, fatal=True)
    else:
        parser.print_help()
        exit()

if __name__ == "__main__":
    main()
