MESSAGES = {
    "unsupported_language": "Skipping '{path}' — language not supported (Python, JS, TS, Go, C, C++ only).",
    "file_not_found":       "Error: '{path}' does not exist.",
    "permission_error":     "Skipping '{path}' — permission denied.",
    "binary_file":          "Skipping '{path}' — binary or non-text file.",
    "syntax_error":         "Skipping '{path}' — could not parse file, possible syntax error.",
    "empty_file":           "Skipping '{path}' — file is empty.",
    "api_error":            "AI analysis failed for '{path}' — check your GROQ_API_KEY or network connection.",
    "profiling_error":      "Profiling failed for '{path}' — skipping benchmark.",
}
 
def handle_error(error_type, path, fatal=False):
    message = MESSAGES.get(error_type, "Unknown error for '{path}'.")
    print(message.format(path=path))
    if fatal:
        exit(1)