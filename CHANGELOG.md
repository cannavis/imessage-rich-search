# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/cannavis/imessage-rich-search/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/cannavis/imessage-rich-search/releases/tag/v0.1.0
