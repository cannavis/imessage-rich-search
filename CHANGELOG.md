# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] — 2026-04-30

### Changed
- **Replaced `mcp` SDK dependency with a stdlib-only MCP server implementation.**
  The package now has **zero runtime dependencies** for the MCP server too,
  not just the CLI. This was driven by a real-world TCC issue:
  Claude Desktop spawns MCP servers as subprocesses, and macOS Full Disk Access
  only propagates from Claude.app to **Apple-signed** children. Homebrew Python
  is third-party signed, so `tccd` denied `chat.db` access. System
  `/usr/bin/python3` is Apple-signed, so it inherits FDA cleanly — but the
  `mcp` SDK requires Python 3.10+, while system Python on macOS 12 / 13 / 14 /
  15 / 26 is 3.9. Going stdlib-only resolves this.
- The `[mcp]` install extra is no longer needed and has been removed.
- Recommended install now uses `--python /usr/bin/python3` to ensure FDA
  inheritance from Claude.app.

### Removed
- `mcp` SDK dependency (was optional; now unnecessary).

## [0.1.0] — 2026-04-30

### Added
- Initial release.
- `search()` Python API: read-only scan of `chat.db`, decoding `payload_data`
  NSKeyedArchiver bplists to extract link preview strings, with substring match
  across body + preview metadata.
- `imessage-rich-search` and `imrs` CLI entry points (human + `--json` output).
- `--contact` filter, `--limit`, `--db` override.
- Optional MCP server (`imessage-rich-search-mcp`) exposing
  `search_imessages_rich(query, contact?, limit?)` to Claude Desktop / Claude.ai.
- README, SECURITY policy, MIT license, CI workflow.

[Unreleased]: https://github.com/cannavis/imessage-rich-search/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/cannavis/imessage-rich-search/releases/tag/v0.2.0
[0.1.0]: https://github.com/cannavis/imessage-rich-search/releases/tag/v0.1.0
