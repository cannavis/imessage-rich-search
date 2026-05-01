"""
imessage-rich-search core.

Full-text search across macOS iMessages including link preview metadata
(title, summary, site name) that Apple stores in `message.payload_data`
as an NSKeyedArchiver bplist.

The basic chat.db `text` column only contains the raw message text. When
a user pastes a URL, Messages.app fetches and stores rich preview metadata
separately in `payload_data` — and indexes it for the in-app search bar.
This module exposes the same surface area to the command line.
"""
from __future__ import annotations

import argparse
import json
import plistlib
import sqlite3
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

CHAT_DB = Path.home() / "Library" / "Messages" / "chat.db"
APPLE_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)


@dataclass
class Match:
    rowid: int
    date: Optional[str]
    is_from_me: bool
    handle: Optional[str]
    text: str
    preview: list
    balloon: Optional[str]


def apple_ns_to_iso(ns: Optional[int]) -> Optional[str]:
    """Convert Apple's nanoseconds-since-2001-01-01 epoch to an ISO 8601 string."""
    if not ns:
        return None
    return (APPLE_EPOCH + timedelta(seconds=ns / 1_000_000_000)).isoformat()


def extract_strings(blob: Optional[bytes]) -> list:
    """Pull human-readable strings from an NSKeyedArchiver binary plist.

    We don't reconstruct the object graph — we just collect every string in
    the `$objects` array, which is sufficient for full-text search and avoids
    a heavy dependency like ccl_bplist or pyobjc.
    """
    if not blob:
        return []
    try:
        plist = plistlib.loads(blob)
    except Exception:
        return []
    out = []
    for o in plist.get("$objects", []):
        if isinstance(o, str) and o and o != "$null" and not o.startswith("$"):
            # Filter out short Foundation class names like 'NSURL', 'NSDate'
            if not (o.startswith("NS") and len(o) < 30):
                out.append(o)
    return out


def search(
    query: str,
    contact: Optional[str] = None,
    limit: int = 200,
    db_path: Path = CHAT_DB,
) -> list:
    """Search messages where text OR extracted preview metadata contains `query`.

    Args:
        query: Case-insensitive substring to match.
        contact: Optional handle filter (e.g. '+14073993471' or 'foo@bar.com').
        limit: Maximum matches to return.
        db_path: Override path to chat.db (defaults to ~/Library/Messages/chat.db).

    Returns:
        List of Match objects, newest first.
    """
    if not db_path.exists():
        raise FileNotFoundError(
            f"chat.db not found at {db_path}. "
            "Grant Full Disk Access to your terminal in System Settings → "
            "Privacy & Security → Full Disk Access."
        )
    q = query.lower()
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    sql = """
        SELECT m.ROWID, m.text, m.date, m.is_from_me,
               m.payload_data, m.balloon_bundle_id, h.id AS handle
        FROM message m
        LEFT JOIN handle h ON m.handle_id = h.ROWID
    """
    params: list = []
    if contact:
        sql += " WHERE h.id = ?"
        params.append(contact)
    sql += " ORDER BY m.date DESC"

    matches: list = []
    for row in cur.execute(sql, params):
        text = row["text"] or ""
        preview = extract_strings(row["payload_data"])
        haystack = (text + "\n" + "\n".join(preview)).lower()
        if q in haystack:
            matches.append(Match(
                rowid=row["ROWID"],
                date=apple_ns_to_iso(row["date"]),
                is_from_me=bool(row["is_from_me"]),
                handle=row["handle"],
                text=text,
                preview=preview,
                balloon=row["balloon_bundle_id"],
            ))
            if len(matches) >= limit:
                break
    conn.close()
    return matches


def _format_human(matches: list, query: str) -> str:
    if not matches:
        return f"No matches for {query!r}.\n"
    lines = [f"{len(matches)} match(es) for {query!r}:\n"]
    for m in matches:
        arrow = "->" if m.is_from_me else "<-"
        lines.append(f"[{m.date}] {arrow} {m.handle or 'me'}  (rowid={m.rowid})")
        if m.text:
            t = m.text[:300].replace("\n", " ")
            lines.append(f"  text: {t}")
        for s in m.preview:
            if query.lower() in s.lower():
                lines.append(f"  * preview: {s[:300]}")
            elif s.startswith("http"):
                lines.append(f"    url:     {s[:300]}")
        lines.append("")
    return "\n".join(lines)


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="imessage-rich-search",
        description="Full-text search across macOS iMessages including link preview metadata.",
    )
    ap.add_argument("query", help="Search term (case-insensitive substring)")
    ap.add_argument("--contact", help="Filter by handle, e.g. +14073993471 or foo@bar.com")
    ap.add_argument("--limit", type=int, default=200, help="Max results (default: 200)")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of human output")
    ap.add_argument(
        "--db",
        type=Path,
        default=CHAT_DB,
        help="Path to chat.db (default: ~/Library/Messages/chat.db)",
    )
    args = ap.parse_args(argv)

    try:
        results = search(args.query, args.contact, args.limit, args.db)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except sqlite3.OperationalError as e:
        print(f"error: cannot open chat.db ({e}). Grant Full Disk Access.", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps([asdict(m) for m in results], indent=2, ensure_ascii=False))
    else:
        sys.stdout.write(_format_human(results, args.query))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
