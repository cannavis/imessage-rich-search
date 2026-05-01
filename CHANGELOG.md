# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] — 2026-04-30

### Fixed
- **MCP server now actually works inside Claude Desktop.** v0.2.0 documented the
  fix incorrectly. Investigation revealed Claude Desktop spawns MCP servers
  through `/Applications/Claude.app/Contents/Helpers/disclaimer`, which calls
  `responsibility_spawnattrs_setdisclaim()` to deliberately break TCC inheritance.
  Result: the spawned binary needs *its own* Full Disk Access grant —
  Claude.app's grant doesn't propagate. The required path is Apple's system
  Python at `/Library/Developer/CommandLineTools/.../python3.9`.

### Added
- `install.sh` — one-command installer that creates a venv against Apple's
  Python and prints exact post-install instructions for Steps 2–4.
- New "Why Apple's Python" section in README explaining the disclaimer / TCC
  responsibility-chain mechanics, with sources.
- README troubleshooting now includes a `log stream` recipe to verify the TCC
  grant is being honored.

### Changed
- README install path now uses a plain `/usr/bin/python3 -m venv` flow (no
  pipx — pipx's own Python often conflicts with system Python's older pip
  internals).
- Troubleshooting table updated to distinguish "CLI denied in terminal" (your
  terminal lacks FDA) from "MCP denied in Claude Desktop" (Apple's python3.9
  lacks FDA — disclaimer in effect).

### Removed
- v0.2.0's incorrect claim that `pipx install --python /usr/bin/python3 ...`
  alone is sufficient. It isn't, because of `disclaimer`.

## [0.2.0] — 2026-04-30

### Changed
- Replaced the `mcp` SDK dependency with a stdlib-only JSON-RPC MCP server.
  The package now has zero runtime dependencies for both CLI and MCP server.

### Removed
- `mcp` SDK dependency (was optional; now unnecessary).

## [0.1.0] — 2026-04-30

### Added
- Initial release.
- `search()` Python API: read-only scan of `chat.db`, decoding `payload_data`
  NSKeyedArchiver bplists to extract link preview strings.
- `imessage-rich-search` and `imrs` CLI entry points (human + `--json` output).
- `--contact`, `--limit`, `--db` flags.
- MCP server entry point exposing `search_imessages_rich(query, contact?, limit?)`.

[Unreleased]: https://github.com/cannavis/imessage-rich-search/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/cannavis/imessage-rich-search/releases/tag/v0.2.1
[0.2.0]: https://github.com/cannavis/imessage-rich-search/releases/tag/v0.2.0
[0.1.0]: https://github.com/cannavis/imessage-rich-search/releases/tag/v0.1.0
