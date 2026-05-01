#!/usr/bin/env bash
# imessage-rich-search installer.
# Sets up a venv against Apple's system /usr/bin/python3 (Apple-signed,
# required for Full Disk Access to propagate via Claude Desktop's
# `disclaimer` spawn wrapper).
set -euo pipefail

VERSION="${IMRS_VERSION:-v0.2.1}"
VENV_DIR="${HOME}/.local/share/imessage-rich-search"
BIN_DIR="${HOME}/.local/bin"
APPLE_PY="/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9"

# Color helpers
B=$'\033[1m'; D=$'\033[2m'; G=$'\033[1;32m'; R=$'\033[1;31m'; Y=$'\033[1;33m'; BL=$'\033[1;34m'; X=$'\033[0m'

step() { printf '%s==>%s %s\n' "$BL" "$X" "$*"; }
ok()   { printf '%s✓%s %s\n'   "$G"  "$X" "$*"; }
warn() { printf '%s!%s %s\n'   "$Y"  "$X" "$*" >&2; }
die()  { printf '%s✗%s %s\n'   "$R"  "$X" "$*" >&2; exit 1; }

# 1. Sanity checks
[[ "$(uname)" == "Darwin" ]] || die "macOS only — detected $(uname)."

step "Checking for Xcode Command Line Tools (provides Apple's signed Python 3.9)"
if ! /usr/bin/xcode-select -p &>/dev/null; then
  warn "Command Line Tools not found. Run:  xcode-select --install"
  warn "Then re-run this installer."
  exit 1
fi
[[ -x "$APPLE_PY" ]] || die "Apple's Python 3.9 not found at: $APPLE_PY
Try: xcode-select --install   (or reinstall Command Line Tools)"
ok "Found $APPLE_PY"

# 2. Create venv with Apple's Python and install package
step "Creating venv at $VENV_DIR"
[[ -d "$VENV_DIR" ]] && rm -rf "$VENV_DIR"
/usr/bin/python3 -m venv "$VENV_DIR"
ok "Venv created"

step "Installing imessage-rich-search@${VERSION}"
"$VENV_DIR/bin/pip" install --upgrade --quiet pip
"$VENV_DIR/bin/pip" install --quiet "git+https://github.com/cannavis/imessage-rich-search@${VERSION}"
ok "Package installed"

# 3. Symlink entry points
step "Linking executables into $BIN_DIR"
mkdir -p "$BIN_DIR"
for exe in imessage-rich-search imrs imessage-rich-search-mcp; do
  ln -sf "$VENV_DIR/bin/$exe" "$BIN_DIR/$exe"
done
ok "Symlinks: imessage-rich-search, imrs, imessage-rich-search-mcp"

# 4. Print post-install instructions (printf-only, no heredoc-substitution traps)
echo
echo "────────────────────────────────────────────────────────────────────────"
printf '%sInstalled.%s  Three manual steps remain:\n' "$G" "$X"
echo "────────────────────────────────────────────────────────────────────────"
echo
printf '%sSTEP 1 — Grant Full Disk Access to Apple'\''s Python 3.9%s\n' "$B" "$X"
echo
echo "    System Settings → Privacy & Security → Full Disk Access"
echo "    Click [+], press ⌘⇧G, paste this path, hit Return:"
echo
echo "        $APPLE_PY"
echo
echo "    Select python3.9, click Open, toggle ON."
echo
printf '%sSTEP 2 — Add the MCP server to Claude Desktop%s\n' "$B" "$X"
echo
echo "    Edit:  ~/Library/Application Support/Claude/claude_desktop_config.json"
echo
echo "    Merge this into the top-level JSON (preserve any existing keys):"
echo
echo '        "mcpServers": {'
echo '          "imessage-rich-search": {'
printf  '            "command": "%s/imessage-rich-search-mcp"\n' "$BIN_DIR"
echo '          }'
echo '        }'
echo
printf '%sSTEP 3 — Restart Claude Desktop%s\n' "$B" "$X"
echo
echo "    ⌘Q (full quit, not just close-window) and relaunch."
echo
echo "────────────────────────────────────────────────────────────────────────"
printf '%sVerify CLI works now (does not need step 1 or 2):%s\n' "$D" "$X"
printf '    %s/imrs "obsidian" --limit 3\n' "$BIN_DIR"
printf '%sUninstall:%s\n' "$D" "$X"
printf '    rm -rf %s && rm -f %s/{imessage-rich-search,imrs,imessage-rich-search-mcp}\n' "$VENV_DIR" "$BIN_DIR"
echo "────────────────────────────────────────────────────────────────────────"
