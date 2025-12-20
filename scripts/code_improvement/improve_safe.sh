#!/usr/bin/env bash
# Conservative code improvement script
# Applies only safe, deterministic formatting and import sorting

set -euo pipefail

echo "Starting conservative code improvements..."
echo "This will only apply formatting and import sorting (safe changes)."
echo ""

# Black formatting (deterministic, safe)
echo "1. Formatting Python code with Black..."
python -m black .

# Ruff import sorting (safe, deterministic)
echo "2. Sorting imports with Ruff..."
python -m ruff check . --select I --fix

echo ""
echo "Safe improvements complete!"
echo "Files have been formatted and imports have been sorted."