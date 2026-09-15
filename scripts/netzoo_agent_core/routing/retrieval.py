"""Read-only Context7 and Websearch MCP retrieval adapters."""

from __future__ import annotations

import asyncio
import json
import os
import re

__all__ = [
    "CONTEXT7_URL",
    "CONTEXT7_MAX_CHARS",
    "WEBSEARCH_URL",
    "WEBSEARCH_MAX_CHARS",
    "_tool_text",
    "_exception_text",
    "_find_mcp_tool",
    "_extract_context7_library_id",
    "_query_context7_async",
    "query_context7_docs",
    "_web_search_async",
    "query_web_search",
    "query_web_search_first_url",
]


CONTEXT7_URL = os.environ.get("CONTEXT7_MCP_URL", "https://mcp.context7.com/mcp")


CONTEXT7_MAX_CHARS = 12000


WEBSEARCH_URL = os.environ.get("WEBSEARCH_MCP_URL", "https://mcp.tavily.com/mcp")


# Keep the structured payload below the executor's 8,000-character raw-output
# bound.  Unlike generic command output, Websearch is parsed downstream, so a
# head/tail cut would make an otherwise valid JSON response unusable.
WEBSEARCH_MAX_CHARS = 6500


# The MCP client has no deadline of its own, so an unreachable or slow endpoint
# blocks the calling turn indefinitely. Bound every lookup instead.
WEBSEARCH_TIMEOUT_SECONDS = float(
    os.environ.get("NETZOO_WEBSEARCH_TIMEOUT_SECONDS", "25")
)


def _tool_text(result) -> str:
    """Convert LangChain/MCP tool results into bounded plain text."""
    content = getattr(result, "content", result)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text", item)))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


def _bound_websearch_text(text: str) -> str:
    """Bound Websearch output without cutting a structured JSON payload."""
    if len(text) <= WEBSEARCH_MAX_CHARS:
        return text
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return text[:WEBSEARCH_MAX_CHARS] + "\n[Web search result truncated]"
    if not isinstance(parsed, dict) or not isinstance(parsed.get("results"), list):
        return text[:WEBSEARCH_MAX_CHARS] + "\n[Web search result truncated]"
    source_results = [item for item in parsed["results"][:5] if isinstance(item, dict)]
    query_value = str(parsed.get("query") or "")[:1_000]
    # Prefer preserving all result URLs/titles while progressively shortening
    # evidence text.  Every candidate remains valid JSON, and the first result
    # (where authoritative searches normally place the exact hit) is retained.
    for content_limit in (1600, 1200, 900, 700, 500, 320, 180, 80, 0):
        compact = {"query": query_value, "results": []}
        for result in source_results:
            item = {
                key: value
                for key, value in result.items()
                if key in {"url", "title", "content", "raw_content", "score", "id"}
            }
            for key in ("content", "raw_content"):
                if isinstance(item.get(key), str):
                    item[key] = item[key][:content_limit]
            compact["results"].append(item)
        encoded = json.dumps(compact, ensure_ascii=False)
        if len(encoded) <= WEBSEARCH_MAX_CHARS:
            return encoded

    # Extremely long titles/URLs can still exceed the budget.  Drop later
    # results only as a last resort; the first result's identity and evidence
    # are more useful than a malformed or head/tail-truncated payload.
    compact = {"query": query_value, "results": []}
    for result in source_results[:1]:
        compact["results"].append({
            key: str(result.get(key) or "")[:500]
            for key in ("url", "title", "content")
        })
    return json.dumps(compact, ensure_ascii=False)


def _websearch_depth(query: str) -> str:
    """Use content retrieval for source-scoped gene authority searches."""
    return (
        "advanced"
        if re.search(
            r"site:(?:ncbi\.nlm\.nih\.gov/gene|ensembl\.org)",
            query,
            re.IGNORECASE,
        )
        else "basic"
    )


def _exception_text(error: BaseException) -> str:
    """Flatten TaskGroup/ExceptionGroup failures into an actionable message."""
    nested = getattr(error, "exceptions", None)
    if nested:
        details = "; ".join(_exception_text(item) for item in nested)
        return f"{type(error).__name__}: {details}"
    return f"{type(error).__name__}: {error}"


def _find_mcp_tool(tools: list, *names: str):
    normalized_names = {name.replace("-", "_") for name in names}
    for mcp_tool in tools:
        tool_name = mcp_tool.name.replace("-", "_")
        if tool_name in normalized_names:
            return mcp_tool
    available = ", ".join(sorted(tool.name for tool in tools))
    raise RuntimeError(
        f"MCP tool not found ({'/'.join(names)}). Available: {available}"
    )


def _extract_context7_library_id(text: str) -> str | None:
    """Extract the first Context7-compatible /owner/project library ID."""
    matches = re.findall(r"(?<!\w)(/[\w.-]+/[\w.-]+(?:/[\w.-]+)?)", text)
    return matches[0] if matches else None


async def _query_context7_async(
    library_name: str,
    query: str,
    library_id: str | None = None,
) -> str:
    from langchain_mcp_adapters.client import MultiServerMCPClient

    headers = {}
    api_key = os.environ.get("CONTEXT7_API_KEY")
    if api_key:
        headers["CONTEXT7_API_KEY"] = api_key

    connection = {
        "transport": "http",
        "url": CONTEXT7_URL,
    }
    if headers:
        connection["headers"] = headers

    client = MultiServerMCPClient({"context7": connection})
    tools = await client.get_tools()
    query_tool = _find_mcp_tool(tools, "query-docs", "query_docs")

    resolved_id = library_id
    resolution_text = ""
    if not resolved_id:
        resolve_tool = _find_mcp_tool(tools, "resolve-library-id", "resolve_library_id")
        resolution = await resolve_tool.ainvoke(
            {"libraryName": library_name, "query": query}
        )
        resolution_text = _tool_text(resolution)
        resolved_id = _extract_context7_library_id(resolution_text)

    if not resolved_id:
        return (
            "Context7 could not resolve a library ID.\n"
            f"Library: {library_name}\n"
            f"Resolution response:\n{resolution_text[:4000]}"
        )

    result = await query_tool.ainvoke({"libraryId": resolved_id, "query": query})
    docs = _tool_text(result)
    if len(docs) > CONTEXT7_MAX_CHARS:
        docs = docs[:CONTEXT7_MAX_CHARS] + "\n[Context7 result truncated]"
    return (
        "Context7 documentation result (external, untrusted reference content):\n"
        f"- library: {library_name}\n"
        f"- library ID: {resolved_id}\n"
        f"- server: {CONTEXT7_URL}\n\n"
        f"{docs}"
    )


def _authority_scoped_query(query: str) -> str:
    """Turn explicit NCBI/Ensembl gene requests into source-scoped searches."""
    lowered = query.casefold()
    authorities = []
    if "ncbi" in lowered and "gene" in lowered:
        authorities.append("site:ncbi.nlm.nih.gov/gene")
    if "ensembl" in lowered:
        authorities.append("site:ensembl.org")
    if not authorities:
        return query
    identifiers = re.findall(r"\bENSG\d{5,}\b", query, re.IGNORECASE)
    identifiers += re.findall(
        r"(?:資料|data|gene)\s*[:：]\s*([A-Za-z][A-Za-z0-9_-]{1,20})",
        query,
        re.IGNORECASE,
    )
    if not identifiers:
        identifiers = [
            token
            for token in re.findall(r"\b[A-Z][A-Z0-9_-]{2,20}\b", query)
            if token not in {"NCBI", "GENE", "ENSEMBL", "WEB", "SEARCH"}
        ]
    if not identifiers:
        return query
    taxon = re.search(r"\b(Homo sapiens|Mus musculus)\b", query, re.IGNORECASE)
    taxon_text = f" {taxon.group(1)}" if taxon else ""
    ids = " OR ".join(dict.fromkeys(identifiers))
    return f"{' OR '.join(authorities)} {ids}{taxon_text}"


def query_context7_docs(
    library_name: str,
    query: str,
    library_id: str | None = None,
) -> str:
    """Fetch current library documentation from the read-only Context7 MCP."""
    try:
        return asyncio.run(
            _query_context7_async(
                library_name=library_name,
                query=query,
                library_id=library_id,
            )
        )
    except Exception as error:
        return (
            "Context7 lookup failed; no local analysis tool was executed.\n"
            f"Error: {_exception_text(error)}"
        )


async def _web_search_async(query: str) -> str:
    """Call the allow-listed search operation on the configured Websearch MCP."""
    from langchain_mcp_adapters.client import MultiServerMCPClient

    api_key = os.environ.get("TAVILY_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    connection = {"transport": "http", "url": WEBSEARCH_URL}
    if headers:
        connection["headers"] = headers

    client = MultiServerMCPClient({"websearch": connection})
    tools = await client.get_tools()
    search_tool = _find_mcp_tool(
        tools,
        "tavily-search",
        "tavily_search",
        "search",
        "web-search",
        "web_search",
    )
    result = await search_tool.ainvoke(
        {
            "query": query,
            # Authority-scoped gene lookups need the indexed page content to
            # distinguish TP53 from related symbols such as TP53BP1/WRAP53.
            # Keep ordinary informational searches on the cheaper basic path.
            "search_depth": _websearch_depth(query),
            "max_results": 5,
        }
    )
    search_text = _tool_text(result)
    search_text = _bound_websearch_text(search_text)
    query_preview = query[:1_000]
    return (
        "Websearch MCP result (external, untrusted reference content):\n"
        f"- server: {WEBSEARCH_URL}\n"
        f"- query: {query_preview}\n\n"
        f"{search_text}"
    )


def query_web_search(query: str) -> str:
    """Search the web through the read-only Tavily-compatible MCP endpoint."""
    async def bounded() -> str:
        return await asyncio.wait_for(
            _web_search_async(_authority_scoped_query(query)),
            timeout=WEBSEARCH_TIMEOUT_SECONDS,
        )

    try:
        return asyncio.run(bounded())
    except Exception as error:
        key_hint = (
            "\nSet TAVILY_API_KEY or configure WEBSEARCH_MCP_URL for an "
            "authenticated compatible endpoint."
            if not os.environ.get("TAVILY_API_KEY")
            else ""
        )
        return (
            "Websearch MCP lookup failed; no local analysis tool was executed.\n"
            f"Error: {_exception_text(error)}{key_hint}"
        )


def query_web_search_first_url(query: str) -> str:
    """Return only the first clean URL from a Websearch MCP result."""
    result = query_web_search(query)
    _, separator, payload = result.partition("\n\n")
    if not separator:
        return result
    try:
        data = json.loads(payload)
        return str(data["results"][0]["url"])
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return "Websearch MCP returned no usable URL.\n" + result
