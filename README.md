# 🔧 codewrench

> Point it at your code. Get back what's slow and how to fix it.

Codewrench is a multi-language performance analyser that combines static analysis with AI-powered explanations. It finds real performance issues in your code — nested loops, inefficient patterns, bad practices — then explains exactly why they're a problem and shows you the fix.

No cloud, no setup hell, no enterprise pricing. Just run it on a file.

---

## Installation

```bash
pip install codewrench
```

Create a `.env` file in your project root:

```
GROQ_API_KEY=your_key_here
```

Get a free Groq API key at [console.groq.com](https://console.groq.com)

---

## Usage

```bash
codewrench yourfile.py
codewrench app.js
codewrench main.go
codewrench ./myproject
```

Codewrench detects the language from the file extension automatically. Point it at a folder and it walks the entire project.

### Example output

```
========================================
         CODEWRENCH REPORT
========================================
Files Scanned  : 1
Languages      : python
Issues Found   : 8 across 1 files
========================================

--- Warnings ---
  Nested loop at line 19 — potential O(n²)
  String concatenation at line 22 — use ''.join() instead
  re.compile() inside loop at line 31 — move it outside, compile once and reuse
  Bare except at line 40 — catches everything, be specific

Top 5 slowest functions BEFORE fix:
  process_data                   cumtime: 2.341s
  build_string                   cumtime: 0.812s

Top 5 slowest functions AFTER fix:
  process_data                   cumtime: 0.421s
  build_string                   cumtime: 0.109s

Want AI analysis? (y/n): y

--- AI Analysis ---

1. Nested loop at line 19
   Problem: Two nested loops over the same data gives you O(n²) complexity.
   For 1000 items that's 1,000,000 iterations instead of 1,000.

Want to apply fixes to files? (y/n): y
  Original saved as yourfile.py.bak
  Fixes applied to yourfile.py

Save report? (y/n): y
  Report saved to codewrench_report.md
```

---

## What it catches

**High priority**
- Nested loops — O(n²) and worse
- Expensive I/O calls inside loops (`open`, `requests`, etc.)
- `re.compile()` inside loops — compile once, reuse
- `print()` / logging inside loops — I/O on every iteration
- `await` inside loops — use `asyncio.gather()` or `Promise.all()`
- Repeated attribute access that should be cached
- String concatenation with `+=` in loops
- String concatenation in nested loops — quadratic complexity
- Unnecessary object creation in loops (`dict()`, `list()`, etc.)

**Medium priority**
- List concat with `+` instead of `.extend()`
- List appends inside nested loops
- Unnecessary `list(range(n))` creation
- Bare `except:` and overly broad `except Exception`
- `try/except` inside loops
- Global variable access inside loops
- Mutable default arguments
- Import inside functions
- `len()` calls inside loops

---

## Supported languages

| Language | Extension |
|----------|-----------|
| Python | `.py` |
| JavaScript | `.js` |
| TypeScript | `.ts` |
| Go | `.go` |
| C | `.c` |
| C++ | `.cpp`, `.cc` |

---

## .wrenchignore

Create a `.wrenchignore` file in your project root to skip files or folders:

```
migrations/
tests/
legacy_code.py
*.min.js
```

Works like `.gitignore` — supports wildcards and directory patterns.

---

## How it works

```
your file
    ↓
Tree-sitter parses it into a syntax tree
    ↓
IR translator converts to language-agnostic representation
    ↓
20 detectors run static analysis on the IR
    ↓
Before/after profiling (Python)
    ↓
Findings sent to Groq (Llama 3.3 70B)
    ↓
Plain English explanation + fix
```

The static analysis layer is deterministic — it either finds a nested loop or it doesn't. No hallucination. The AI layer explains what the detectors already confirmed exists.

---

## Roadmap

- [x] Static analysis (Python, JS, TS, Go, C, C++)
- [x] AI-powered explanations and fixes
- [x] Multi-language IR architecture
- [x] Runtime profiling — before/after benchmark (Python)
- [x] 20 detectors across high and medium priority
- [x] Folder support with recursive analysis
- [x] `.wrenchignore` support
- [x] Smart API batching — one call per folder, not per file
- [x] `pip install codewrench`
- [ ] Multi-language profiling (Node, Go, gcc)
- [ ] Language-specific detectors
- [ ] Git diff integration — analyse only what changed
- [ ] VS Code extension
- [ ] Web UI

---

## Project structure

```
wrench/
├── detectors/
│   ├── base.py          ← depth tracking, core visitor
│   ├── high.py          ← high priority detectors
│   └── medium.py        ← medium priority detectors
├── languages/
│   ├── python_rules.py  ← Tree-sitter node mappings per language
│   ├── js_rules.py
│   ├── ts_rules.py
│   ├── go_rules.py
│   ├── c_rules.py
│   └── cpp_rules.py
├── profilers/
│   └── profiler.py      ← cProfile integration
├── ir.py                ← language-agnostic IR node
├── ir_translator.py     ← Tree-sitter → IR translation
├── parser_engine.py     ← language detection + parser setup
├── ai_engine.py         ← Groq integration
├── report.py            ← Layer 5 report and output
├── errors.py            ← error handling
├── wrenchignore.py      ← .wrenchignore support
└── main.py              ← entry point
```

---

## Contributing

Pull requests welcome. If you want to add a new language, add a rules file in `languages/` mapping Tree-sitter node types to the generic IR types. That's it — the detectors work on all languages automatically.

Open an issue first for anything major.

---

Built by [Vishad Jain](https://github.com/vishaddjain)