#!/usr/bin/env bash
# Code improvement suggestions script
# Shows what would be changed without modifying any files

set -euo pipefail

echo "Code improvement suggestions (no files will be modified)"
echo "======================================================"
echo ""

# Black formatting check with diff
echo "== Black Formatting (check + diff; no changes) =="
python -m black . --check --diff || true
echo ""

# Ruff imports check only
echo "== Ruff Import Sorting (check only; no changes) =="
python -m ruff check . --select I || true
echo ""

# Ruff full lint check only
echo "== Ruff Full Linting (check only; no changes) =="
python -m ruff check . || true
echo ""

echo "======================================================"
echo "Suggestions complete! No files were modified."
echo "To apply safe improvements, run: make improve-safe"
echo "Or run: ./scripts/code_improvement/improve_safe.sh"