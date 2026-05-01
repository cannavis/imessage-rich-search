"""
Stdlib-only MCP server for imessage-rich-search.

Implements just enough of the Model Context Protocol (JSON-RPC 2.0 over
newline-delimited STDIO) to expose `search_imessages_rich` as a tool —
no third-party dependencies. This matters because:

  Claude Desktop spawns MCP servers as subprocesses. macOS TCC propagates
  Full Disk Access from Claude.app to subprocesses ONLY when the spawned
  binary is Apple-signed. Homebrew's python3.x is third-party signed →
  TCC denies. Apple's /usr/bin/python3 (3.9 on macOS 12+) is Apple-signed
  → TCC inherits cleanly. So the server must run on stdlib only.

Spec reference: https://modelcontextprotocol.io/specification (2025-06-18).
"""
from __future__ import annotations

import json
import sys
import traceback
from dataclasses import asdict
from typing import Any, Dict, Optional

from . import __version__
from .cli import search

PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "imessage-rich-search"

TOOLS = [
    {
        "name": "search_imessages_rich",
        "description": (
            "Full-text search across macOS iMessages including link preview metadata "
            "(title, summary, site name) that Apple stores in payload_data — content "
            "the basic chat.db text column does not expose. Returns newest-first matches "
            "where the query (case-insensitive substring) appears in either the message "
            "body OR the rich link preview."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Substring to search for (case-insensitive).",
                },
                "contact": {
                    "type": "string",
                    "description": "Optional handle filter, e.g. '+14073993471' or 'name@example.com'.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max matches to return (default 50).",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 1000,
                },
            },
            "required": ["query"],
        },
    }
]


def _send(msg: Dict[str, Any]) -> None:
    """Write a single JSON-RPC message to stdout, newline-delimited."""
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _ok(msg_id: Any, result: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _err(msg_id: Any, code: int, message: str, data: Any = None) -> Dict[str, Any]:
    err: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": msg_id, "error": err}


def _handle_initialize(msg_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    return _ok(msg_id, {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {"tools": {"listChanged": False}},
        "serverInfo": {"name": SERVER_NAME, "version": __version__},
    })


def _handle_tools_list(msg_id: Any) -> Dict[str, Any]:
    return _ok(msg_id, {"tools": TOOLS})


def _handle_tools_call(msg_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    name = params.get("name")
    args = params.get("arguments") or {}

    if name != "search_imessages_rich":
        return _err(msg_id, -32602, f"unknown tool: {name!r}")

    query = args.get("query")
    if not isinstance(query, str) or not query:
        return _err(msg_id, -32602, "'query' is required and must be a non-empty string")
    contact = args.get("contact")
    if contact is not None and not isinstance(contact, str):
        return _err(msg_id, -32602, "'contact' must be a string if provided")
    limit = args.get("limit", 50)
    if not isinstance(limit, int) or limit < 1 or limit > 1000:
        return _err(msg_id, -32602, "'limit' must be an integer in [1, 1000]")

    try:
        results = [asdict(m) for m in search(query, contact, limit)]
    except FileNotFoundError as e:
        return _ok(msg_id, {
            "content": [{"type": "text", "text": f"error: {e}"}],
            "isError": True,
        })
    except Exception as e:
        return _ok(msg_id, {
            "content": [{
                "type": "text",
                "text": f"error: {type(e).__name__}: {e}\n{traceback.format_exc()}",
            }],
            "isError": True,
        })

    summary = (
        f"{len(results)} match(es) for {query!r}"
        + (f" (contact={contact})" if contact else "")
    )
    return _ok(msg_id, {
        "content": [
            {"type": "text", "text": summary},
            {"type": "text", "text": json.dumps(results, ensure_ascii=False, indent=2)},
        ],
        "structuredContent": {"matches": results, "count": len(results)},
        "isError": False,
    })


def _handle(msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return a response dict, or None for notifications (no response)."""
    method = msg.get("method")
    msg_id = msg.get("id")
    params = msg.get("params") or {}

    if msg_id is None:
        # Notification — no response. We just ignore unknown ones gracefully.
        return None

    if method == "initialize":
        return _handle_initialize(msg_id, params)
    if method == "tools/list":
        return _handle_tools_list(msg_id)
    if method == "tools/call":
        return _handle_tools_call(msg_id, params)
    if method == "ping":
        return _ok(msg_id, {})

    return _err(msg_id, -32601, f"method not found: {method!r}")


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as e:
            _send(_err(None, -32700, f"parse error: {e}"))
            continue
        try:
            response = _handle(msg)
        except Exception as e:
            response = _err(msg.get("id"), -32603, f"internal error: {type(e).__name__}: {e}")
        if response is not None:
            _send(response)


if __name__ == "__main__":
    main()
