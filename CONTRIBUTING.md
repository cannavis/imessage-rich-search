# Contributing

Thanks for considering a contribution.

## Quick start

```bash
git clone https://github.com/cannavis/imessage-rich-search
cd imessage-rich-search
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[mcp,dev]"
ruff check .
```

## Pull requests

- Branch from `main`. Keep PRs focused — one logical change each.
- Run `ruff check .` and `python -m compileall -q src` before pushing.
- Update `CHANGELOG.md` under `[Unreleased]` for any user-visible change.
- Add or update README sections for any new flag or behavior.
- The CLI must remain **dependency-free** (stdlib only). New runtime deps
  belong only behind an `[extra]` in `pyproject.toml`.

## Bug reports

Use the issue template. Always include:

- macOS version (`sw_vers`)
- Python version (`python3 --version`)
- Tool version (`imessage-rich-search --help` shows the package version once installed)
- Reproduction: exact command, redacted output

**Never paste real `chat.db` content into a public issue.** Redact phone
numbers, names, and message bodies before sharing.

## Privacy when contributing

If you need to share a sample to reproduce a bug:

- Generate a synthetic `chat.db` (the schema is documented widely online), or
- Build a minimal repro with `sqlite3 :memory:` in the test itself.

Don't attach real chat data, even your own — issues are public and indexed.

## Style

- Python: ruff defaults plus the lint rules in `pyproject.toml`. 100-char lines.
- No emoji in code or commit messages. Plain ASCII in CLI output.
- Type hints encouraged but not enforced.
- Commit messages: imperative mood, ≤72-char subject. Example:
  `add --regex flag for substring search`
