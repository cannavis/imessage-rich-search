"""
MCP server exposing `search_imessages_rich` to Claude Desktop / Claude.ai.

Wraps the same `search()` function that the CLI uses, so behavior is
identical across both surfaces.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Optional

from mcp.server.fastmcp import FastMCP

from .cli import search

mcp = FastMCP("imessage-rich-search")


@mcp.tool()
def search_imessages_rich(
    query: str,
    contact: Optional[str] = None,
    limit: int = 50,
) -> list:
    """Search macOS iMessages including link preview metadata.

    Returns matches where the query (case-insensitive substring) appears in
    either the message body OR the rich link preview (title/summary/site)
    that Messages.app stores in payload_data — content the basic iMessage
    tool cannot see.

    Args:
        query: Substring to search for (case-insensitive).
        contact: Optional handle filter, e.g. "+14073993471" or "x@y.com".
        limit: Maximum matches to return (default 50).

    Returns:
        Newest-first list of {rowid, date, is_from_me, handle, text, preview, balloon}.
    """
    return [asdict(m) for m in search(query, contact, limit)]


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
