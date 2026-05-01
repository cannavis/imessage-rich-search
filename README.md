# imessage-rich-search

> Full-text search across macOS iMessages — **including the link preview metadata** (titles, summaries, site names) that Messages.app indexes but the raw `chat.db` text column never exposes.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Platform: macOS](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](#requirements)
[![No deps](https://img.shields.io/badge/runtime%20deps-zero-brightgreen.svg)](#how-it-works)
[![MCP](https://img.shields.io/badge/MCP-compatible-8A2BE2.svg)](#claude-desktop-mcp-server)

## The problem this solves

When you paste a URL into iMessage, macOS fetches a rich preview — title, summary, site name, hero image — and stores that metadata in `chat.db` as an NSKeyedArchiver blob in `message.payload_data`. **Messages.app's search bar reads it. The raw `chat.db` `text` column does not.**

So if a friend sent `https://x.com/foo/status/123` and the preview card said *"Obsidian + Claude Code is the most underrated productivity stack"* — searching for "obsidian" in any tool that only reads `text` returns **zero results**. Messages.app finds it. This tool finds it. They search the same surface.

## What it is — and isn't

**Is:** A read-only, local search over your `chat.db`. ~200 lines of stdlib Python. Zero runtime dependencies. CLI + optional MCP server for Claude Desktop.

**Isn't:** A Messages replacement (no UI, no send/edit/delete). A way to access anyone else's messages. An iCloud sync tool — searches only what's locally on this Mac. An OCR / image / audio / sticker reader. A bypass for Full Disk Access — you must grant it explicitly.

## Requirements

| | |
|---|---|
| **OS** | macOS 11 Big Sur or newer (tested through macOS 26) |
| **Architecture** | Apple Silicon (arm64) or Intel (x86_64) |
| **Python** | Apple's system `/usr/bin/python3` (3.9, ships with Xcode Command Line Tools) — required, see [Why Apple's Python](#why-apples-python) |
| **Permissions** | One specific Full Disk Access grant — see [Step 2](#install) |
| **Disk** | ~30 KB code + ~15 MB venv |

If you don't have Command Line Tools, run `xcode-select --install` first.

## Install

### Step 1 — Run the installer (one command)

```bash
curl -fsSL https://raw.githubusercontent.com/cannavis/imessage-rich-search/main/install.sh | bash
```

What this does, in plain English:
1. Verifies you're on macOS with Command Line Tools.
2. Creates a virtual environment at `~/.local/share/imessage-rich-search` against Apple's system Python 3.9.
3. Pulls and installs this package from GitHub into that venv.
4. Symlinks three commands into `~/.local/bin`: `imessage-rich-search`, `imrs` (alias), `imessage-rich-search-mcp`.

If you'd rather not pipe `curl` into `bash`, do it manually:

```bash
/usr/bin/python3 -m venv ~/.local/share/imessage-rich-search
~/.local/share/imessage-rich-search/bin/pip install --upgrade pip
~/.local/share/imessage-rich-search/bin/pip install "git+https://github.com/cannavis/imessage-rich-search@v0.2.1"
mkdir -p ~/.local/bin
for exe in imessage-rich-search imrs imessage-rich-search-mcp; do
  ln -sf ~/.local/share/imessage-rich-search/bin/$exe ~/.local/bin/$exe
done
```

The CLI works immediately after this:

```bash
~/.local/bin/imrs "obsidian" --limit 3
```

If your shell can't find `imrs`, add `~/.local/bin` to your PATH:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && exec zsh
```

### Step 2 — Grant Full Disk Access to Apple's Python 3.9

**You must add this exact path to FDA, or the MCP server (and any disclaimed call into chat.db) will fail with `authorization denied`.** This step does not affect the CLI when run from your own terminal.

1. Open **System Settings → Privacy & Security → Full Disk Access**.
2. Click the **+** button.
3. In the file picker, press **⌘ + Shift + G** (Go to Folder).
4. Paste this path **exactly**:

   ```
   /Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin
   ```

5. Hit Return — you'll see the contents of that `bin` folder.
6. Select **`python3.9`** (not `python3`, which is a symlink).
7. Click **Open**. It appears in the list as `python3.9`.
8. Make sure the toggle is **ON**. Authenticate if prompted.

### Step 3 — Wire the MCP server into Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` and merge this in (preserve any existing keys):

```json
{
  "mcpServers": {
    "imessage-rich-search": {
      "command": "/Users/YOUR_USERNAME/.local/bin/imessage-rich-search-mcp"
    }
  }
}
```

Replace `YOUR_USERNAME` with your actual username (`whoami` will tell you).

### Step 4 — Restart Claude Desktop

**⌘Q** (full quit — not just close-window) and relaunch. New chats will have a `search_imessages_rich` tool.

## Verify it works

CLI:
```bash
imrs "obsidian" --limit 3
# 3 match(es) for 'obsidian':
# [2026-04-08T22:56:23+00:00] -> +1XXXXXXXXXX  (rowid=...)
#   * preview: Claude Code + Obsidian Ultimate Guide (build an AI second brain)
```

MCP server (manual JSON-RPC handshake — same path Claude Desktop uses):
```bash
(printf '%s\n%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"0"}}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search_imessages_rich","arguments":{"query":"obsidian","limit":1}}}') \
| /Applications/Claude.app/Contents/Helpers/disclaimer ~/.local/bin/imessage-rich-search-mcp
```

You should see two JSON-RPC responses. If the second one contains `"isError": true` and `"authorization denied"`, Step 2 (FDA grant) was missed or the toggle is off.

## Usage

```bash
imrs "obsidian"                                  # search all conversations
imrs "obsidian" --contact "+14073993471"         # restrict to one handle
imrs "claude code" --json | jq '.[].preview[0]'  # JSON for piping
imrs "obsidian" --limit 20 --db /backup/chat.db  # backup file
imessage-rich-search --help                      # full options
```

Output legend: `->` sent · `<-` received · `*` preview hit · `rowid` cross-references back into `chat.db`.

## Claude Desktop (MCP server)

Once Steps 1–4 above are done, Claude can call this tool directly:

```
search_imessages_rich(query, contact?, limit?)
```

- `query` — case-insensitive substring (required)
- `contact` — optional handle filter, e.g. `"+14073993471"` or `"name@example.com"`
- `limit` — max matches, default 50

Returns newest-first matches with body, decoded preview metadata, handle, date, and rowid.

## Why Apple's Python

This isn't arbitrary — it's the only thing that works inside Claude Desktop, and there's a clear reason:

Claude Desktop spawns MCP servers through `/Applications/Claude.app/Contents/Helpers/disclaimer`, a tiny wrapper that calls `responsibility_spawnattrs_setdisclaim()`. This is an Apple API that **deliberately breaks the TCC responsibility chain** so the MCP server is treated as its own responsible process. The intent: prevent third-party MCP servers from silently inheriting Claude.app's broad permissions.

Consequence: the spawned binary needs *its own* Full Disk Access grant — Claude.app's grant doesn't propagate. macOS resolves the venv's `python3` to its canonical Apple binary at `/Library/Developer/CommandLineTools/.../python3.9`, and that's the path TCC checks. Hence Step 2.

If you install with Homebrew Python or pyenv instead, the canonical path resolves somewhere else and TCC blocks the request. Apple's CLT Python is the path of least resistance.

References:
- [Qt: The Curious Case of the Responsible Process](https://www.qt.io/blog/the-curious-case-of-the-responsible-process)
- [Michael Tsai's notes on `responsibility_spawnattrs_setdisclaim`](https://mjtsai.com/blog/2025/07/07/the-curious-case-of-the-responsible-process/)

## How it works

```
chat.db (SQLite, opened with mode=ro)
  └─ message
       ├─ text                 ← raw text (what basic tools see)
       ├─ payload_data  BLOB   ← NSKeyedArchiver bplist of LPLinkMetadata
       │                         (title, summary, site, image refs)
       └─ balloon_bundle_id    ← e.g. com.apple.messages.URLBalloonProvider

For every row matching the contact filter:
  1. Read text + payload_data
  2. plistlib.loads(payload_data) → walk $objects → collect strings
  3. haystack = (text + '\n'.join(preview_strings)).lower()
  4. Match if query.lower() in haystack
```

Walking strings out of `$objects` avoids needing `ccl_bplist`, `pyobjc`, or full NSKeyedUnarchiver — for full-text search the leaf strings are all that matter.

## Privacy & security

- **Read-only.** Opens `chat.db` with SQLite URI flag `mode=ro`.
- **Local-only.** No network calls. (`grep -r 'urllib\|requests\|http\|socket' src/` returns nothing.)
- **No telemetry.**
- **Zero runtime dependencies** — nothing to be supply-chain-attacked through.
- The FDA grant from Step 2 applies to Apple's system Python 3.9 system-wide. If you have `Terminal`, `bash`, or `Visual Studio Code` already in FDA, this isn't expanding your attack surface — those can already trivially shell out to `/usr/bin/python3`.

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

## Limitations

- **Substring match only.** No FTS5, regex, or boolean operators. (Roadmap.)
- **Local DB only.** If a message lives only in iCloud and isn't synced to this Mac's `chat.db`, this tool won't see it.
- **Preview metadata depends on Messages.app having fetched it.** If a link card never loaded (offline send, expired URL), there's no `payload_data` to search.
- **String extraction is lossy by design.** Image MIME types, dimension tuples like `{0, 0}`, and profile-image URLs may appear in raw output. They don't affect search hits.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `imrs: command not found` | Add `~/.local/bin` to PATH: `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && exec zsh` |
| `unable to open database file` from CLI in your terminal | Add your terminal app to FDA: System Settings → Privacy & Security → Full Disk Access. ⌘Q + relaunch the terminal. |
| `authorization denied` from Claude Desktop's MCP call (CLI works fine) | Step 2 is missing or toggled off. Verify `python3.9` is in FDA list with toggle ON. ⌘Q + relaunch Claude Desktop. |
| Claude Desktop doesn't see the tool at all | Validate JSON: `python3 -c "import json; json.load(open('$HOME/Library/Application Support/Claude/claude_desktop_config.json'))"`. Then ⌘Q + relaunch. |
| Returns 0 matches but Messages.app finds them | Wrong `--contact` format. Drop `--contact` to confirm. Phone numbers must be E.164: `+14155551212`. |
| Apple's Python 3.9 isn't at the expected path | `xcode-select -p` to verify CLT is installed. If installed but path differs (e.g., full Xcode), find it: `xcrun --find python3` |
| Search slow on huge DBs | Linear scan + bplist parse per row. ~100k message DBs take a few seconds. FTS5 index is roadmap. |

### Verify the TCC grant directly

If unsure whether Step 2 took effect, watch the system log while making a request:

```bash
log stream --predicate 'process == "tccd"' --info | grep -E "python3\.9|chat\.db|SystemPolicyAllFiles"
```

You want to see `Auth Right: Allowed (System Set)` for the `python3.9` binary. `Denied (Service Policy)` means the grant isn't in place.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and PRs welcome. Don't paste real chat content into public issues — redact phone numbers, names, and message text first.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT — see [LICENSE](LICENSE).
