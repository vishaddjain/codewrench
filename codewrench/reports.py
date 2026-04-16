import shutil
import os
from .ai_engine import analyse, get_fixed_code

CONFIDENCE_ORDER = ["high", "medium", "low"]
CONFIDENCE_LABELS = {
    "high": "🔴 High",
    "medium": "🟡 Medium",
    "low": "🟢 Low",
}

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

def build_report_stats(all_results):
    confidence_counts = {level: 0 for level in CONFIDENCE_ORDER}
    type_counts = {}
    file_summaries = []

    for filepath, warnings in all_results.items():
        per_file_counts = {level: 0 for level in CONFIDENCE_ORDER}
        for warning in warnings:
            confidence = warning.get("confidence", "medium")
            if confidence not in confidence_counts:
                confidence = "medium"
            confidence_counts[confidence] += 1
            per_file_counts[confidence] += 1

            issue_type = warning["message"].split(" at line ")[0].split(" — ")[0]
            type_counts[issue_type] = type_counts.get(issue_type, 0) + 1

        total = len(warnings)
        file_summaries.append((filepath, total, per_file_counts))

    file_summaries.sort(key=lambda item: (-item[1], item[0]))
    top_issue_types = sorted(type_counts.items(), key=lambda item: (-item[1], item[0]))[:5]
    top_files = file_summaries[:5]

    return confidence_counts, top_issue_types, top_files, file_summaries

def write_confidence_section(f, title, confidence, all_results):
    f.write(f"## {title}\n\n")
    matching_files = []
    for filepath, warnings in all_results.items():
        filtered = [w for w in warnings if w.get("confidence", "medium") == confidence]
        if filtered:
            matching_files.append((filepath, sorted(filtered, key=lambda w: w["line"])))

    if not matching_files:
        f.write("No issues in this confidence band.\n\n")
        return

    for filepath, warnings in matching_files:
        f.write(f"### {filepath} ({len(warnings)} issue{'s' if len(warnings) != 1 else ''})\n\n")
        for warning in warnings:
            f.write(f"- Line {warning['line']}: {warning['message']}\n")
        f.write("\n")

def save_report(files_scanned, languages, all_results, analysis=None):
    total_issues = sum(len(w) for w in all_results.values())
    confidence_counts, top_issue_types, top_files, _ = build_report_stats(all_results)

    with open("codewrench_report.md", "w", encoding="utf8") as f:
        f.write("# Codewrench Report\n\n")
        f.write("## Summary\n\n")
        f.write(f"- Files scanned: {files_scanned}\n")
        f.write(f"- Files with issues: {len(all_results)}\n")
        f.write(f"- Total issues: {total_issues}\n")
        f.write(f"- Languages: {', '.join(sorted(languages))}\n\n")

        f.write("### Confidence Breakdown\n\n")
        for level in CONFIDENCE_ORDER:
            f.write(f"- {CONFIDENCE_LABELS[level]}: {confidence_counts[level]}\n")
        f.write("\n")

        if top_issue_types:
            f.write("### Top Issue Types\n\n")
            for issue_type, count in top_issue_types:
                f.write(f"- {issue_type}: {count}\n")
            f.write("\n")

        if top_files:
            f.write("### Top Affected Files\n\n")
            for filepath, total, counts in top_files:
                f.write(
                    f"- {filepath}: {total} issues "
                    f"({counts['high']} high, {counts['medium']} medium, {counts['low']} low)\n"
                )
            f.write("\n")

        f.write("---\n\n")

        write_confidence_section(f, "High Confidence", "high", all_results)
        write_confidence_section(f, "Medium Confidence", "medium", all_results)
        write_confidence_section(f, "Low Confidence", "low", all_results)

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
