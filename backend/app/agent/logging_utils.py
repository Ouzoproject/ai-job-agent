import json
import logging
import os



VERBOSE = os.environ.get("AGENT_VERBOSE") == "1"

if not VERBOSE:
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def _preview(value, max_len: int = 200) -> str:
    """Shorten a string for logging."""
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    text = text.replace("\n", " ")
    return text if len(text) <= max_len else text[:max_len] + "…"


def _content_text(result) -> str:
    """Join the text parts of a tool result's `content` blocks."""
    return " ".join(getattr(block, "text", "") or "" for block in result.content)


def _tool_message_payload(result):
    """What we send back to the LLM for a tool call."""
    if result.is_error:
        return {"error": _content_text(result)}

    if result.structured_content is not None:
        return result.structured_content

    return _content_text(result)


def _summarize_tool_result(result) -> str:
    """
    Summarize a tool call result for logging. If VERBOSE=1, the raw result is printed instead.
    """

    if VERBOSE:
        return str(result)

    if result.is_error:
        return f"ERROR: {_preview(_content_text(result))}"

    # If the tool returned structured content, summarize it.
    payload = (
        result.structured_content.get("result")
        if result.structured_content is not None
        else None
    )
    # If no structured content, summarize the raw content instead.
    if payload is None:
        return _preview(_content_text(result))

    # Summarize the structured content based on its type. If it's a list, show the first few items;
    # if it's a dict, show key fields; otherwise, just preview it.
    if isinstance(payload, list):
        count = len(payload)
        if count == 0:
            return "0 results"
        lines = [
            f"  - {item.get('title', item.get('id', '?'))} "
            f"@ {item.get('company', '?')} ({', '.join(item.get('locations', []) or ['?'])})"
            for item in payload[:5]
            if isinstance(item, dict)
        ]
        more = f"\n  … and {count - 5} more" if count > 5 else ""
        return f"{count} result(s):\n" + "\n".join(lines) + more

    if isinstance(payload, dict):
        title = payload.get("title", "?")
        company = payload.get("company", "?")
        line = f"{title} @ {company}"
        description = payload.get("description")
        if description:
            line += f"\n  description preview: {_preview(description, 150)}"
        return line

    return _preview(payload)
