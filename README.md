# imessage-rich-search

> Full-text search across macOS iMessages — including the **link preview metadata** (titles, summaries, site names) that Messages.app indexes but the raw `chat.db` text column never exposes.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Platform: macOS](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](#requirements)
[![No deps](https://img.shields.io/badge/runtime%20deps-zero-brightgreen.svg)](#how-it-works)
[![MCP](https://img.shields.io/badge/MCP-compatible-8A2BE2.svg)](#use-as-an-mcp-server-claude-desktop)

## The problem this solves

When you paste a URL into iMessage, macOS fetches a rich preview — title, summary, site name, hero image — and stores that metadata in `chat.db` as an NSKeyedArchiver blob in `message.payload_data`. Messages.app's search bar reads it. The basic `chat.db` `text` column does not contain it.

So if a friend sent you `https://x.com/foo/status/123` and the preview card said *"Obsidian + Claude Code is the most underrated productivity stack"* — searching for "obsidian" in any tool that only reads `text` returns **zero results**. Messages.app finds it. This tool finds it. They search the same surface area.
</p>

## Features

- Searches message body **and** decoded link preview metadata in one pass
- Filter by handle (phone / email)
- Human-readable or JSON output
- Read-only on `chat.db` (uses SQLite URI mode)
- Zero runtime dependencies for the CLI (Python stdlib only)
- Optional MCP server so Claude Desktop / Claude.ai can call it directly
- Newest-first results, ISO 8601 timestamps, direction arrows, rowid for cross-reference

## What it is — and isn't

**Is:**
- A read-only forensic / archival search over your local `chat.db`
- A drop-in companion to MCP iMessage tools that only see raw text
- ~200 lines of stdlib Python

**Is not:**
- A Messages.app replacement (no UI, no send/edit/delete)
- A way to access anyone else's messages
- An iCloud / cross-device sync tool — searches **only** what's locally on this Mac
- A bypass for Full Disk Access — you must grant it explicitly
- An OCR / image / audio / sticker / handwriting reader (only text + link metadata)
- A way to recover deleted messages beyond what SQLite still holds

## Requirements

| | |
|---|---|
| **OS** | macOS 11 Big Sur or newer (tested through macOS 26) |
| **Architecture** | Apple Silicon (arm64) or Intel (x86_64) |
| **Python** | 3.9+ for the CLI · 3.10+ for the optional MCP server |
| **Disk** | Negligible (~50 KB installed) |
| **Permissions** | **Full Disk Access** for the terminal/app that runs the script |

The `chat.db` schema fields it relies on (`text`, `payload_data`, `balloon_bundle_id`, `handle.id`) have been stable since macOS 10.13 High Sierra; this tool will likely work further back than its officially-claimed floor, untested.

## Install

### Option A — `pipx` (recommended)

`pipx` isolates the tool in its own venv. Install pipx first if needed:

```bash
brew install pipx
pipx ensurepath
```

Then install this tool from GitHub:

```bash
# CLI only
pipx install "git+https://github.com/cannavis/imessage-rich-search"

# CLI + MCP server (requires Python 3.10+)
pipx install --python python3.14 "imessage-rich-search[mcp] @ git+https://github.com/cannavis/imessage-rich-search"
```

### Option B — `pip` into a venv

```bash
git clone https://github.com/cannavis/imessage-rich-search
cd imessage-rich-search
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[mcp]"
```

### Option C — single-file, no install

The CLI module has zero deps. You can curl it and run:

```bash
curl -O https://raw.githubusercontent.com/cannavis/imessage-rich-search/main/src/imessage_rich_search/cli.py
python3 cli.py "obsidian"
```

## Grant Full Disk Access (one-time, required)

`chat.db` is locked behind macOS TCC. Without FDA you'll get `unable to open database file`.

1. Open **System Settings → Privacy & Security → Full Disk Access**
2. Click **+** and add the app you'll run this from:
   - Running `imessage-rich-search` directly in the shell? → add **Terminal** (or **iTerm**, **Warp**, **Ghostty**, **Alacritty**, etc. — whichever terminal you actually use)
   - Running it from Claude Desktop via MCP? → add **Claude.app**
   - Running it from a script editor or IDE? → add that app
3. **Quit and relaunch** that app fully (⌘Q, not just close-window) for the permission to take effect
4. Verify: `python3 -c "import sqlite3; sqlite3.connect('file:'+__import__('os').path.expanduser('~/Library/Messages/chat.db')+'?mode=ro', uri=True).execute('SELECT COUNT(*) FROM message').fetchone()"` — should print a number, not raise

## Usage

```bash
# Basic search across all conversations
imessage-rich-search "obsidian"

# Restrict to one contact
imessage-rich-search "obsidian" --contact "+14073993471"

# JSON for piping into jq, scripts, or another tool
imessage-rich-search "obsidian" --contact "+14073993471" --json | jq '.[].preview[0]'

# Limit results, point at a backup chat.db
imessage-rich-search "claude code" --limit 20 --db /path/to/chat.db

# Short alias
imrs "obsidian"

# Module form (no entry point needed)
python3 -m imessage_rich_search "obsidian"
```

### Output

```
6 match(es) for 'obsidian':

[2026-04-08T22:56:23+00:00] -> +14073993471  (rowid=234953)
    url:     https://x.com/aiedge_/status/2041908011078447222?s=42
  * preview: Claude Code + Obsidian Ultimate Guide (build an AI second brain)
...
```

`->` = sent · `<-` = received · `*` = preview line containing your query · `rowid` = cross-reference key into `chat.db`.

## Use as an MCP server (Claude Desktop)

Lets Claude Desktop call the search directly during conversations.

1. Install with the `mcp` extra (see Option A above with `[mcp]`)
2. Find the entry-point absolute path: `which imessage-rich-search-mcp`
3. Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

   ```json
   {
     "mcpServers": {
       "imessage-rich-search": {
         "command": "/full/path/from/which/imessage-rich-search-mcp"
       }
     }
   }
   ```

4. Make sure **Claude.app** has Full Disk Access (System Settings → Privacy & Security)
5. **Quit and relaunch** Claude Desktop fully

Claude can now call `search_imessages_rich(query, contact?, limit?)` as a tool.

## How it works

```
chat.db (SQLite, read-only)
  └─ message
       ├─ text                     ← raw text (what basic tools see)
       ├─ payload_data  (BLOB)     ← NSKeyedArchiver bplist of LPLinkMetadata
       │                              (title, summary, site, image refs)
       └─ balloon_bundle_id        ← e.g. com.apple.messages.URLBalloonProvider

For every row:
  1. Read text + payload_data
  2. plistlib.loads(payload_data) → walk $objects → collect strings
  3. Lower-case haystack = text + "\n".join(preview_strings)
  4. Match if query.lower() in haystack
```

The "walk strings out of $objects" trick avoids needing `ccl_bplist`, `pyobjc`, or full NSKeyedUnarchiver semantics — for full-text search we don't care about the object graph, only the leaf strings.

## Privacy & security

- **Read-only.** Opens `chat.db` with SQLite URI flag `mode=ro`.
- **Local-only.** No network calls. Ever. (`grep -r 'urllib\|requests\|http' src/` returns nothing.)
- **No telemetry.**
- **No data leaves your Mac** unless you choose to share output.
- The CLI has zero runtime dependencies — nothing to be supply-chain-attacked through.
- See [SECURITY.md](SECURITY.md) for vulnerability reporting.

## Limitations

- **Substring match only.** No FTS5 ranking, no regex, no boolean operators. Add it if you want it (`PR welcome`).
- **Local DB only.** If a message lives only in iCloud and isn't synced to this Mac's `chat.db`, it won't appear.
- **Preview metadata depends on Messages.app having fetched it.** If the link card never loaded (offline send, expired URL), there's no `payload_data` to search.
- **String-extraction is lossy by design.** It pulls every string from the bplist; you may occasionally see image MIME types, dimension tuples like `{0, 0}`, or profile-image URLs in the preview list. They don't affect search hits but do appear in raw output.
- **Full Disk Access is a hard requirement** — there is no workaround.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `unable to open database file` / `cannot open chat.db` | Full Disk Access not granted to the running app. Add app, then ⌘Q + relaunch. |
| Returns 0 matches but Messages.app finds them | Wrong `--contact` format (must match the `handle.id` in `chat.db` — typically `+1XXXXXXXXXX` or full email). Run without `--contact` to confirm. |
| `No module named 'mcp'` when starting the MCP server | Install with the extra: `pipx install "imessage-rich-search[mcp] @ git+..."` |
| Claude Desktop doesn't see the tool | Verify JSON syntax in `claude_desktop_config.json`, fully quit Claude (⌘Q), relaunch. |
| Search is slow on huge databases | The current implementation does a linear scan + bplist parse per row. For 100k+ message DBs, expect a few seconds. An FTS5 virtual-table backed index is on the roadmap. |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and PRs welcome.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgments

- Apple's `chat.db` schema, which has been remarkably stable across a decade of macOS releases
- The folks who reverse-engineered `payload_data` / `LPLinkMetadata` over the years
- [Model Context Protocol](https://modelcontextprotocol.io) for the MCP spec
