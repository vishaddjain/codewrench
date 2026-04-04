import shutil
import os
from .ai_engine import analyse, get_fixed_code

def print_summary(files_scanned, languages, all_results):
    total_issues = sum(len(w) for w in all_results.values())
    print("=" * 40)
    print("CODEWRENCH REPORT".center(40))
    print("=" * 40)
    print(f"Files Scanned  : {files_scanned}")
    print(f"Languages      : {', '.join(languages)}")
    print(f"Issues Found   : {total_issues} across {len(all_results)} files")
    print("=" * 40)

def print_profiling(before_stats, after_stats=None):
    print("\n--- Performance Profile ---\n")
    print("Top 5 slowest functions:")
    for stat in before_stats[:5]:
        func = stat['function'].split(":")[-1]
        print(f"  {func:<30} cumtime: {stat['cumtime']}s")

    if after_stats is not None:
        print("\nTop 5 slowest functions AFTER fix:")
        for stat in after_stats[:5]:
            func = stat['function'].split(":")[-1]
            print(f"  {func:<30} cumtime: {stat['cumtime']}s")

def ask_and_analyse(code, warnings):
    if not os.getenv("GROQ_API_KEY"):
        print("\nAI analysis unavailable — add GROQ_API_KEY to .env to enable.")
        return
    print("\n--- AI Analysis ---\n")
    result = analyse(code, warnings)
    print(result)

def ask_and_apply_fixes(code, warnings, filepath, no_backup=False):
    if not os.getenv("GROQ_API_KEY"):
        print("\nAI analysis unavailable — add GROQ_API_KEY to .env to enable.")
        return

    fixed_code = get_fixed_code(code, warnings)
    with open(filepath + ".bak", "w", encoding="utf8") as f:
        f.write(code)
    with open(filepath, "w", encoding="utf8") as f:
        f.write(fixed_code)
    print(f"Original saved as {filepath}.bak")
    print(f"Fixes applied to {filepath}")
    if no_backup:
        os.remove(filepath + ".bak")
        print("Backup removed.")
    else:
        print(f"Backup kept at {filepath}.bak")

def save_report(files_scanned, languages, all_results, analysis=None):
    total_issues = sum(len(w) for w in all_results.values())
    
    with open("codewrench_report.md", "w", encoding="utf8") as f:
        # header
        f.write("# Codewrench Report\n\n")
        f.write(f"**Files Scanned:** {files_scanned}\n\n")
        f.write(f"**Languages:** {', '.join(languages)}\n\n")
        f.write(f"**Issues Found:** {total_issues} across {len(all_results)} files\n\n")
        f.write("---\n\n")

        # warnings per file
        f.write("## Warnings\n\n")
        for filepath, warnings in all_results.items():
            f.write(f"### {filepath}\n\n")
            for w in warnings:
                f.write(f"- {w}\n")
            f.write("\n")

        # AI analysis
        if analysis:
            f.write("---\n\n")
            f.write("## AI Analysis\n\n")
            f.write(analysis)
            f.write("\n")

    print("Report saved to codewrench_report.md")


def revert_file(filepath):
    bak_path = filepath + ".bak"
    if os.path.exists(bak_path):
        shutil.copy(bak_path, filepath)
        os.remove(bak_path)
        print(f"Reverted {filepath} from {bak_path}")
    else:
        print(f"No backup found for {filepath} — nothing to revert.")
