#!/bin/bash
# Dependency Security Audit Script
# Runs pip-audit on requirements files and generates reports

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Running dependency security audit..."

# Check if pip-audit is available
if ! python3 -c "import pip_audit" 2>/dev/null; then
    echo "Installing pip-audit..."
    pip3 install pip-audit
fi

# Create reports directory
mkdir -p reports

# Audit main requirements
echo "Auditing requirements.txt..."
python3 -m pip_audit --requirement requirements.txt > reports/dependency_audit_requirements.txt 2>&1 || true

# Audit dev requirements if it exists
if [ -f requirements-dev.txt ]; then
    echo "Auditing requirements-dev.txt..."
    python3 -m pip_audit --requirement requirements-dev.txt > reports/dependency_audit_dev.txt 2>&1 || true
fi

# Generate JSON reports
echo "Generating JSON reports..."
python3 -m pip_audit --requirement requirements.txt --format json > reports/dependency_audit_requirements.json 2>&1 || true

if [ -f requirements-dev.txt ]; then
    python3 -m pip_audit --requirement requirements-dev.txt --format json > reports/dependency_audit_dev.json 2>&1 || true
fi

echo "Audit complete. Reports saved to reports/dependency_audit_*.txt and *.json"
echo ""
echo "Summary:"
grep -i "vulnerability\|found" reports/dependency_audit_requirements.txt | head -10 || echo "No vulnerabilities found in requirements.txt"
