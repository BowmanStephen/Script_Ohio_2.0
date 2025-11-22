#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "📦 Script Ohio 2.0 bootstrap (repo: ${REPO_ROOT})"

function ensure_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "[ERROR] Required command '$cmd' not found in PATH."
    exit 1
  fi
}

ensure_command "python3"
ensure_command "npm"
ensure_command "brew"

echo "→ Ensuring TypeScript CLI (tsc) is installed..."
if command -v tsc >/dev/null 2>&1; then
  tsc --version
else
  npm install -g typescript@latest
  tsc --version
fi

echo "→ Checking TOON Format CLI availability..."
if npx @toon-format/cli --version >/dev/null 2>&1; then
  echo "  TOON CLI available via npx"
else
  echo "  [WARN] TOON CLI not available via npx. Install with: npm install -g @toon-format/cli"
  echo "  Note: TOON format features will work via npx even without global install"
fi

echo "→ Ensuring Kiota CLI (and dotnet runtime) via Homebrew..."
if command -v kiota >/dev/null 2>&1; then
  kiota --version
else
  brew install kiota
  kiota --version
fi

echo "→ Checking dotnet runtime..."
if command -v dotnet >/dev/null 2>&1; then
  dotnet --version
else
  echo "[WARN] dotnet command not found even after Kiota install. Install manually:"
  echo "       brew install --cask dotnet-sdk"
fi

echo "→ Optional: enable corepack/pnpm support for API v2 work..."
if command -v corepack >/dev/null 2>&1; then
  corepack enable >/dev/null 2>&1 || true
  corepack prepare pnpm@latest --activate
else
  echo "[WARN] corepack not available; skip pnpm activation."
fi

echo "✅ Development tooling verified. Ready to run demos and tests."

