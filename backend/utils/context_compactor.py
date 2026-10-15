from typing import List, Dict, Any

def compact_tool_output(output: str, max_chars: int = 4000) -> str:
    """
    Truncates redundant middle sections of large tool outputs while
    preserving head and tail diagnostics.
    """
    if not isinstance(output, str):
        output = str(output)

    if len(output) <= max_chars:
        return output

    half = max_chars // 2
    head = output[:half]
    tail = output[-half:]
    omitted = len(output) - max_chars
    return f"{head}\n\n... [Omitted {omitted} characters of intermediate output for context efficiency] ...\n\n{tail}"

def compact_context(context: List[Dict[str, Any]], max_chars_per_record: int = 4000) -> List[Dict[str, Any]]:
    """
    Produces a compacted copy of agent execution context for downstream reasoning.
    """
    compacted = []
    for item in context:
        new_item = dict(item)
        if "response" in new_item and isinstance(new_item["response"], str):
            new_item["response"] = compact_tool_output(new_item["response"], max_chars_per_record)
        compacted.append(new_item)
    return compacted
