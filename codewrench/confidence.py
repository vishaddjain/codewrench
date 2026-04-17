TEST_FILE_SUPPRESS_PREFIXES = (
    "Attribute '",
     "List concatenation with '+'",
)

TEST_FILE_STRONG_DOWNGRADE_PREFIXES = (
    "Potential N+1 query",
    "I/O call ",
    "Linear search",
    "Import is at function level",
     "List concatenation with '+'",
     "Nested loop",
)

SUPPORT_FILE_SUPPRESS_PREFIXES = (
    "Import is at function level",
    "print()/logging call inside loop",
)

SUPPORT_FILE_STRONG_DOWNGRADE_PREFIXES = (
    "Bare except",
    "Overly broad 'except Exception'",
)

def score_warning(warning, context):
    confidence = warning["confidence"]
    function = warning["function"]
    message = warning["message"]

    if context.is_tutorial_file:
        return None

    if context.is_script_file or context.is_tutorial_file:
        if message.startswith(SUPPORT_FILE_STRONG_DOWNGRADE_PREFIXES):
            if confidence == "high":
                confidence = "low"
            elif confidence == "medium":
                return None
            elif confidence == "low":
                return None

        if confidence == "high":
            confidence = "medium"
        elif confidence == "medium":
            confidence = "low"
        elif confidence == "low":
            return None

    if context.is_test_file:
        if message.startswith(TEST_FILE_SUPPRESS_PREFIXES):
            return None

        if message.startswith(TEST_FILE_STRONG_DOWNGRADE_PREFIXES):
            if confidence == "high":
                confidence = "low"
            elif confidence == "medium":
                return None
            elif confidence == "low":
                return None

        if confidence == "medium":
            confidence = "low"
        elif confidence == "low":
            return None  

    ctx = context.function_contexts.get(function, None) if function else None

    if ctx:
        if ctx["is_cold"]:
            if confidence == "high":
                confidence = "medium"
            elif confidence == "medium":
                confidence = "low"
            elif confidence == "low":
                return None

        if ctx["is_hot"]:
            if confidence == "medium":
                confidence = "high"

        if ctx["call_count"] == 1 and not ctx["is_hot"]:
            if confidence == "low":
                return None

    warning["confidence"] = confidence
    return warning


def filter_warnings(warnings, context, show_all=False):
    if show_all:
        return warnings

    scored = []
    for w in warnings:
        result = score_warning(w, context)
        if result is not None:
            scored.append(result)
        
    return [w for w in scored if w["confidence"] in ("high", "medium")]
