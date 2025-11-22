#!/usr/bin/env python3
"""Fail CI if agents import requests directly instead of using CFBDClient."""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import List

AGENTS_ROOT = Path("agents")
ALLOWED_PREFIXES = [AGENTS_ROOT / "core", AGENTS_ROOT / "system", AGENTS_ROOT / "tools"]
ALLOWED_FILES = {AGENTS_ROOT / "conversational_ai_agent.py"}  # example: external APIs


def _is_allowed(file_path: Path) -> bool:
    return any(_is_relative_to(file_path, prefix) for prefix in ALLOWED_PREFIXES) or file_path in ALLOWED_FILES


def _is_relative_to(path: Path, other: Path) -> bool:
    try:
        path.relative_to(other)
        return True
    except ValueError:
        return False


def _find_violations() -> List[Path]:
    violations: List[Path] = []
    for file_path in AGENTS_ROOT.rglob("*.py"):
        if _is_allowed(file_path):
            continue
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(alias.name == "requests" for alias in node.names):
                    violations.append(file_path)
                    break
            if isinstance(node, ast.ImportFrom) and node.module == "requests":
                violations.append(file_path)
                break
    return violations


def main() -> None:
    violations = _find_violations()
    if violations:
        print("The following agent files import requests directly. Use CFBDClient/GraphQLClient instead:")
        for path in violations:
            print(f" - {path}")
        sys.exit(1)
    print("CFBD client compliance check passed.")


if __name__ == "__main__":
    main()
