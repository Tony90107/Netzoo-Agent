"""Small, bounded public source identities from untrusted lookup results."""

from __future__ import annotations

import json


def web_source_refs(raw_output: str) -> list[dict[str, str]]:
    """Keep source titles and URLs without copying retrieved page content."""
    if not raw_output.startswith("Websearch MCP result"):
        return []
    _, separator, body = raw_output.partition("\n\n")
    if not separator:
        return []
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, dict) or not isinstance(parsed.get("results"), list):
        return []
    refs: list[dict[str, str]] = []
    for item in parsed["results"][:5]:
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        if not isinstance(url, str) or len(url) > 500 or not url.startswith(("https://", "http://")):
            continue
        title = item.get("title")
        refs.append({"title": title[:160] if isinstance(title, str) else "", "url": url})
    return refs
