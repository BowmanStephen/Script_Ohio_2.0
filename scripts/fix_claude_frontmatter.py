#!/usr/bin/env python3
"""
Idempotent Claude agent frontmatter fixer.
Ensures each agent file has a valid YAML frontmatter with a name field.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Configuration
FILES = [
    (Path(".claude/agents/comprehensive-test-agent.md"), "Comprehensive Test Agent"),
    (Path(".claude/agents/test-agent.md"), "Test Agent"),
    (Path(".claude/agents/prompt-library-generator.md"), "Prompt Library Generator"),
]

# Regex patterns
FRONTMATTER_OPEN = re.compile(r"^\s*---\s*$")
NAME_LINE = re.compile(r"^\s*name\s*:\s*(.+?)\s*$", re.IGNORECASE)


def find_frontmatter_bounds(
    lines: list[str], scan_limit: int = 200
) -> tuple[int, int] | None:
    """
    Find the bounds of YAML frontmatter.
    Returns (start_index, end_index) inclusive indices of the --- ... --- block.
    """
    if not lines:
        return None
    if not FRONTMATTER_OPEN.match(lines[0]):
        return None

    max_i = min(len(lines) - 1, scan_limit)
    for i in range(1, max_i + 1):
        if FRONTMATTER_OPEN.match(lines[i]):
            return (0, i)

    return None  # malformed: opened but not closed within scan limit


def ensure_name(file_path: Path, expected_name: str) -> bool:
    """
    Ensure the file has valid frontmatter with the expected name field.
    Returns True if changes were made, False if no changes needed.
    """
    try:
        text = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"ERROR: Could not read {file_path}: {e}", file=sys.stderr)
        return False

    # Preserve trailing newline behavior
    had_trailing_newline = text.endswith("\n")
    lines = text.splitlines()

    bounds = find_frontmatter_bounds(lines)

    if bounds is None:
        # No frontmatter found
        if lines and FRONTMATTER_OPEN.match(lines[0]):
            # Malformed frontmatter - fail fast to avoid corruption
            raise RuntimeError(
                f"{file_path}: malformed frontmatter (opening '---' without closing '---' near top)"
            )

        # Prepend new frontmatter
        new_lines = [
            "---",
            f"name: {expected_name}",
            "---",
            "",
            *lines,
        ]
        out = "\n".join(new_lines) + ("\n" if had_trailing_newline or lines else "\n")

        try:
            file_path.write_text(out, encoding="utf-8")
            print(f"UPDATED: {file_path} (prepended frontmatter)")
            return True
        except Exception as e:
            print(f"ERROR: Could not write {file_path}: {e}", file=sys.stderr)
            return False

    # Has valid frontmatter
    start, end = bounds
    frontmatter_lines = lines[start + 1 : end]

    # Check if name field already exists
    if any(NAME_LINE.match(l) for l in frontmatter_lines):
        print(f"OK: {file_path} (name already present)")
        return False

    # Insert name field after opening ---
    new_lines = lines[: start + 1] + [f"name: {expected_name}"] + lines[start + 1 :]
    out = "\n".join(new_lines) + ("\n" if had_trailing_newline else "")

    try:
        file_path.write_text(out, encoding="utf-8")
        print(f"UPDATED: {file_path} (inserted name into existing frontmatter)")
        return True
    except Exception as e:
        print(f"ERROR: Could not write {file_path}: {e}", file=sys.stderr)
        return False


def main():
    """Main execution function."""
    changed_files = 0

    for file_path, expected_name in FILES:
        try:
            if ensure_name(file_path, expected_name):
                changed_files += 1
        except Exception as e:
            print(f"FATAL: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"Frontmatter fixes complete. Files changed: {changed_files}")
    return changed_files


if __name__ == "__main__":
    sys.exit(main() if main() is not None else 0)
