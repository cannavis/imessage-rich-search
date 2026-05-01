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

step() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m✓\033[0m %s\n'   "$*"; }
warn() { printf '\033[1;33m!\033[0m %s\n'   "$*" >&2; }
die()  { printf '\033[1;31m✗\033[0m %s\n'   "$*" >&2; exit 1; }

# 1. Sanity checks
[[ "$(uname)" == "Darwin" ]] || die "macOS only — detected $(uname)."

step "Checking for Xcode Command Line Tools (provides Apple's signed Python 3.9)"
if ! /usr/bin/xcode-select -p &>/dev/null; then
  warn "Command Line Tools not found. Run:  xcode-select --install"
  warn "Then re-run this installer."
  exit 1
fi
[[ -x "$APPLE_PY" ]] || die "Apple's Python 3.9 not found at:
  $APPLE_PY
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

# 4. Tell the user exactly what's next
cat <<EOF

────────────────────────────────────────────────────────────────────────
$(printf '\033[1;32mInstalled.\033[0m')  Two manual steps remain:
────────────────────────────────────────────────────────────────────────

$(printf '\033[1mSTEP 1 — Grant Full Disk Access to Apple's Python 3.9\033[0m')

    System Settings → Privacy & Security → Full Disk Access
    Click [+], press ⌘⇧G, paste this path, hit Return:

        $APPLE_PY

    Select python3.9, click Open, toggle ON.

$(printf '\033[1mSTEP 2 — Add the MCP server to Claude Desktop\033[0m')

    Edit:  ~/Library/Application Support/Claude/claude_desktop_config.json

    Add this to the top-level JSON (merge into existing "mcpServers" if
    you already have one):

        "mcpServers": {
          "imessage-rich-search": {
            "command": "$BIN_DIR/imessage-rich-search-mcp"
          }
        }

$(printf '\033[1mSTEP 3 — Restart Claude Desktop\033[0m')

    ⌘Q (full quit, not just close-window) and relaunch.

────────────────────────────────────────────────────────────────────────
$(printf '\033[2mVerify CLI works now (does not need step 1 or 2):\033[0m')
    $BIN_DIR/imrs "obsidian" --limit 3
$(printf '\033[2mUninstall:\033[0m')
    rm -rf $VENV_DIR && rm -f $BIN_DIR/{imessage-rich-search,imrs,imessage-rich-search-mcp}
────────────────────────────────────────────────────────────────────────
EOF
