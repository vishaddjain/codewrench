# Changelog

All notable changes to codewrench will be documented here.

---

## [0.2.0] — 2026-04-06

### Added
- `--profile` flag — profiling is now opt-in, no longer runs on every analysis
- `--profile --fix` shows before/after performance comparison
- `--profile` alone profiles the original file without applying fixes
- 5 new detectors (total: 24):
  - **N+1 Query** — flags ORM calls inside loops (Django, SQLAlchemy, general DB patterns)
  - **Linear Search** — flags `.index()` and `.count()` on lists inside loops (O(n) operations)
  - **JS `for...in` on arrays** — suggests `for...of` or `.forEach()` instead
  - **Go goroutine in loops** — flags unbounded goroutine spawning, suggests worker pool
  - **C++ pass by value** — flags large types (`vector`, `string`, `map` etc.) passed without `const&`

### Fixed
- Integer `+=` no longer flagged as string concatenation (COUNTER_NAMES heuristic)
- Integer `+` no longer flagged as list concatenation
- Mutable default detector no longer fires on type annotations (e.g. `def foo(x: List[str] = None)`)
- `''.join()` fix hint no longer suggested for JavaScript — now correctly suggests `array.join('')`
- Duplicate list concatenation warnings on chained expressions (e.g. `a + b + c`)
- `get_fixed_code` no longer called when `--fix` is not passed — eliminates wasteful API call

### Improved
- Expanded `CHEAP_CALLS` — `append`, `pop`, `keys`, `items`, `values`, `extend`, `update`, `get`, `add`, `remove`, `copy`, `clear`, `discard`, and common builtins no longer flagged as expensive
- Dotted method calls (e.g. `list.append`) now correctly matched against `CHEAP_CALLS`
- Language passed to all detectors — enables language-aware warning messages

---

## [0.1.3] — 2026

### Added
- Initial PyPI release
- Static analysis via Tree-sitter + language-agnostic IR
- 20 detectors across high and medium priority
- Runtime profiling — cProfile (Python), execution time (Node.js, Go)
- AI-powered explanations and fixes via Groq (Llama 3.3 70B)
- Folder support with recursive analysis
- `.wrenchignore` support
- CLI flags: `--analyse`, `--fix`, `--save-report`, `--no-backup`, `--revert`
- Supported languages: Python, JavaScript, TypeScript, Go, C, C++