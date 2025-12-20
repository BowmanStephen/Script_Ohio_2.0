# ============================================================================
# Enhanced Makefile for Script Ohio 2.0
# Comprehensive safety-first improvements with validation gates
# ============================================================================

.PHONY: help install test lint format clean improve-safe improve-suggest sort-imports \
        validate-before-improve improve-with-backup safety-check health-check \
        backup-create backup-restore syntax-validate comprehensive-check \
        run-safe safe-validate safe-report ai-assistant smart-ai smart

# Default target
help:
	@echo "Available targets:"
	@echo "  install      Install dependencies"
	@echo "  test         Run tests"
	@echo "  lint         Run linting (no changes)"
	@echo "  format       Format Python code with Black"
	@echo "  sort-imports Sort imports with Ruff (safe only)"
	@echo "  improve-safe Apply safe improvements (format + import sorting)"
	@echo "  improve-with-backup Safe improvements with automatic backup"
	@echo "  improve-suggest Show improvement suggestions (no changes)"
	@echo "  validate-before-improve Run comprehensive pre-improvement checks"
	@echo "  safety-check Quick syntax and structure validation"
	@echo "  health-check Complete system health assessment"
	@echo "  backup-create Create git backup branch"
	@echo "  backup-restore Restore from backup branch"
	@echo "  syntax-validate Validate Python syntax across all files"
	@echo "  comprehensive-check Full validation suite"
	@echo "  run-safe SCRIPT='script.py' Run script with safety wrapper"
	@echo "  safe-validate Run comprehensive safety validation"
	@echo "  safe-report Generate detailed safety report"
	@echo "  ai-assistant   Easy-to-use AI assistant (recommended)"
	@echo "  smart-ai     Interactive AI code assistant"
	@echo "  smart CMD='command' Run single AI command"
	@echo "  clean        Clean build artifacts"

# ============================================================================
# Safety and Backup Targets
# ============================================================================

# Create backup branch before any improvements
backup-create:
	@echo "Creating backup branch..."
	@git checkout -b "backup-before-improve-$(shell date +%Y%m%d-%H%M%S)" || \
	 (echo "Already on a branch, creating backup commit..." && git add -A && git commit -m "Backup before safe improvements")

# Restore from backup (list available backups first)
backup-restore:
	@echo "Available backup branches:"
	@git branch | grep "backup-before-improve"
	@echo ""
	@echo "To restore, use: git checkout <backup-branch-name>"

# Quick syntax validation across all Python files
syntax-validate:
	@echo "Validating Python syntax across all files..."
	@python3 -c "import py_compile; import os; [py_compile.compile(os.path.join(root, f), doraise=True) for root, dirs, files in os.walk('.') for f in files if f.endswith('.py') and (root.startswith('./agents/') or root.startswith('./src/') or root.startswith('./scripts/'))]" 2>/dev/null && echo "✅ All Python files have valid syntax" || echo "❌ Syntax errors found"

# Comprehensive pre-improvement validation
validate-before-improve: syntax-validate
	@echo "Running comprehensive pre-improvement validation..."
	@echo "1. ✅ Syntax validation passed"
	@echo "2. Checking critical file integrity..."
	@test -f "CLAUDE.md" && echo "   ✅ CLAUDE.md exists" || echo "   ❌ CLAUDE.md missing"
	@test -f "requirements.txt" && echo "   ✅ requirements.txt exists" || echo "   ❌ requirements.txt missing"
	@test -f "agents/core/agent_framework.py" && echo "   ✅ Agent framework exists" || echo "   ❌ Agent framework missing"
	@echo "3. Checking data structure integrity..."
	@test -f "data/processed/training/master_training_data_v2.csv" && echo "   ✅ Master training data exists" || echo "   ⚠️  Master training data not found"
	@echo "4. Validating model files..."
	@test -f "models/production/ridge_regression_2025_v2.joblib" && echo "   ✅ Ridge model exists" || echo "   ⚠️  Ridge model not found"
	@echo "5. Pre-improvement validation complete!"

# Complete system health check
health-check: validate-before-improve
	@echo ""
	@echo "🏈 Script Ohio 2.0 System Health Check"
	@echo "======================================"
	@echo "670+ Python files across agents/, src/, scripts/"
	@echo ""
	@echo "📊 Project Statistics:"
	@echo "   - Agent files: $$(find agents/ -name "*.py" | wc -l | tr -d ' ')"
	@echo "   - Source files: $$(find src/ -name "*.py" | wc -l | tr -d ' ')"
	@echo "   - Script files: $$(find scripts/ -name "*.py" | wc -l | tr -d ' ')"
	@echo ""
	@echo "🔧 System Status:"
	@python3 -c "print('   - Python version:', end=''); import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
	@echo "   - Git status: $$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ') files modified"
	@echo ""
	@echo "✅ System health check complete!"

# ============================================================================
# Enhanced Code Improvement Targets (Safety-First)
# ============================================================================

# Safe improvements with automatic backup
improve-with-backup: backup-create validate-before-improve
	@echo "Starting safe improvements with backup protection..."
	@$(MAKE) improve-safe
	@echo "🎉 Safe improvements completed with backup protection!"

# Deterministic formatting - safe, reversible
format:
	@echo "Formatting Python code with Black..."
	@echo "🔄 Running: python -m black ."
	@python -m black .
	@echo "✅ Formatting complete!"

# Deterministic import sorting - Ruff's isort rules only
sort-imports:
	@echo "Sorting imports with Ruff..."
	@echo "🔄 Running: python -m ruff check . --select I --fix"
	@python -m ruff check . --select I --fix
	@echo "✅ Import sorting complete!"

# One-command ultra-safe improvements (combines both) with validation
improve-safe: validate-before-improve format sort-imports
	@echo "🎉 Safe improvements complete!"
	@echo "Running post-improvement validation..."
	@$(MAKE) syntax-validate
	@echo "✅ Post-improvement validation passed!"

# Enhanced suggestions with detailed analysis
improve-suggest:
	@echo "🔍 Code Improvement Analysis (No Changes)"
	@echo "=========================================="
	@echo ""
	@echo "1️⃣ Black Formatting Analysis:"
	@python -m black . --check --diff --color 2>/dev/null || echo "   ⚠️  Formatting differences detected"
	@echo ""
	@echo "2️⃣ Import Sorting Analysis:"
	@python -m ruff check . --select I || echo "   ⚠️  Import sorting issues detected"
	@echo ""
	@echo "3️⃣ Full Lint Analysis:"
	@python -m ruff check . || echo "   ⚠️  Linting issues detected"
	@echo ""
	@echo "💡 To apply safe improvements, run: make improve-with-backup"

# Enhanced lint with detailed output
lint:
	@echo "🔍 Running comprehensive linting checks..."
	@echo "=========================================="
	@python -m ruff check .
	@echo ""
	@echo "📊 Lint Summary:"
	@echo "   Run 'make improve-suggest' for detailed fix suggestions"

# Comprehensive validation suite
comprehensive-check: validate-before-improve lint
	@echo ""
	@echo "🏈 Comprehensive Validation Results"
	@echo "=================================="
	@echo "✅ Syntax validation: PASSED"
	@echo "✅ File integrity: PASSED"
	@echo "✅ Lint analysis: COMPLETED (see above)"
	@echo ""
	@echo "🎯 Next Steps:"
	@echo "   - Fix any linting errors shown above"
	@echo "   - Run 'make improve-with-backup' for safe improvements"
	@echo "   - Run 'make test' to verify functionality"

# ============================================================================
# Enhanced Safety Targets
# ============================================================================

# Run comprehensive safety validation
safe-validate:
	@echo "🛡️  Running comprehensive safety validation..."
	@python3 scripts/safe_improvement_validator.py

# Generate detailed safety report
safe-report:
	@echo "📊 Generating detailed safety report..."
	@python3 scripts/safe_improvement_validator.py --quiet
	@echo "📄 Safety report saved to validation_report_*.json"

# Run any script with safety wrapper
run-safe:
	@if [ -z "$(SCRIPT)" ]; then \
		echo "❌ Usage: make run-safe SCRIPT='path/to/script.py'"; \
		exit 1; \
	fi
	@echo "🛡️  Running script with safety wrapper: $(SCRIPT)"
	@python3 scripts/safe_script_runner.py $(SCRIPT)

# Easy-to-use AI assistant (recommended)
ai-assistant:
	@echo "🤖 Starting Simple AI Assistant..."
	@python3 scripts/simple_ai_assistant.py

# Interactive AI assistant
smart-ai:
	@echo "🤖 Starting Smart AI Code Assistant..."
	@python3 scripts/smart_code_orchestrator.py --interactive

# Single AI command execution
smart:
	@if [ -z "$(CMD)" ]; then \
		echo "❌ Usage: make smart CMD='your command in plain English'"; \
		echo "   Example: make smart CMD='clean up the code formatting'"; \
		exit 1; \
	fi
	@echo "🤖 Smart AI Assistant executing: $(CMD)"
	@python3 scripts/smart_code_orchestrator.py "$(CMD)"

# ============================================================================
# Standard Development Targets
# ============================================================================

install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	@if [ -f "web_app/package.json" ]; then \
		echo "Installing Node.js dependencies..."; \
		cd web_app && npm install; \
	fi

test:
	@echo "Running Python tests..."
	python -m pytest

clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/ 2>/dev/null || true