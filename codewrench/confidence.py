def score_warning(warning, file_context, function_contexts):
    confidence = warning["confidence"]
    function = warning["function"]

    if file_context:
        if confidence == "medium":
            confidence = "low"
        elif confidence == "low":
            return None  

    ctx = function_contexts.get(function, None) if function else None

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
        result = score_warning(w, context.is_test_file, context.function_contexts)
        if result is not None:
            scored.append(result)
        
    return [w for w in scored if w["confidence"] in ("high", "medium")]