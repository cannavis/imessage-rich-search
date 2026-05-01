# Security policy

## Threat model

This tool reads — never writes — the local `chat.db` SQLite file under
`~/Library/Messages/`. It runs only on the machine the user installs it on.
It performs **no network I/O** (verifiable: `grep -r 'urllib\|requests\|http\|socket' src/`
should return nothing).

The CLI has **zero runtime dependencies**; only the optional `[mcp]` extra
introduces a third-party dep (`modelcontextprotocol/python-sdk`).

## Reporting a vulnerability

If you find a security issue — particularly anything involving:

- Reading data outside the user-specified `chat.db`
- Writing or modifying anything (the tool should be strictly read-only)
- Network exfiltration in any code path
- Path-traversal, SQL injection, or bplist-parsing crashes that leak content
- Privilege escalation around Full Disk Access

**Do not open a public issue.** Instead:

- Open a [GitHub private security advisory](https://github.com/cannavis/imessage-rich-search/security/advisories/new), or
- Email the maintainer (see GitHub profile)

You'll get an acknowledgment within 7 days. We aim to ship a fix or mitigation
within 30 days for high-severity issues.

## Supported versions

Only the latest minor release on `main` receives security fixes.

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅        |
| < 0.1   | ❌        |

## What's deliberately out of scope

- **macOS sandboxing / TCC bypass.** Full Disk Access is required and intentional.
  This tool is not a privilege-escalation vector — if you can read `chat.db`
  with `cat`, you can read it with this.
- **Encrypted chat.db backups.** This tool reads the live, in-place SQLite file,
  not encrypted iOS / iCloud backups.
- **Defending against a compromised local user account.** If an attacker
  has shell access as you, they don't need this tool.
