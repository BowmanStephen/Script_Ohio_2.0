from __future__ import annotations

import argparse
import shutil
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

# Cleanup helper for removing non-essential Script Ohio 2.0 artifacts.
# The script operates on a curated allowlist of directories and files that are
# safe to delete without affecting the production pipeline (agents, CFBD
# integration, ML models, and weekly analysis workflow). It defaults to a dry
# run, so you can preview removals before applying the changes.


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class CleanupTarget:
    """Definition of a removable target relative to the repository root."""

    pattern: str
    description: str


REMOVAL_GROUPS: dict[str, Sequence[CleanupTarget]] = {
    "high": (
        CleanupTarget("archive", "Legacy archive artifacts"),
        CleanupTarget("backup", "Backup directory (redundant)"),
        CleanupTarget("legacy", "Legacy code and data"),
        CleanupTarget("model_pack copy", "Duplicate model pack"),
        CleanupTarget("starter_pack copy", "Duplicate starter pack"),
        CleanupTarget("Claude Examples", "Claude prompt examples"),
        CleanupTarget("60 - Prompt Library", "Legacy prompt library"),
        CleanupTarget("week14", "Week 14 consolidated outputs"),
        CleanupTarget("predictions/week12", "Legacy Week 12 prediction outputs"),
        CleanupTarget("predictions/week13", "Legacy Week 13 prediction outputs"),
        CleanupTarget("week14_*_agent.py", "Week 14 one-off agent scripts"),
        CleanupTarget("week14_*.json", "Week 14 JSON outputs"),
        CleanupTarget("cache", "Transient CFBD cache data"),
        CleanupTarget("outputs", "Generated outputs (rebuildable)"),
        CleanupTarget("exports", "Exported artifacts"),
        CleanupTarget("temp", "Temporary files"),
        CleanupTarget("state", "Local state cache"),
    ),
    "medium": (
        CleanupTarget("logs", "Historical run logs"),
        CleanupTarget("project_management", "Project management artifacts"),
        CleanupTarget("documentation", "Duplicated documentation set"),
        CleanupTarget("week13_system_validation.py", "Week 13 validation script"),
        CleanupTarget("week12_digestible_analysis", "Week 12 digestible analysis"),
        CleanupTarget("analysis/week12", "Old Week 12 analysis outputs"),
        CleanupTarget("analysis/week13", "Old Week 13 analysis outputs"),
        CleanupTarget("validation/week13", "Week 13 validation artifacts"),
        CleanupTarget("prediction_*_agent.py", "Ad-hoc prediction diagnostic agents"),
        CleanupTarget("check_key.py", "Debug key inspection script"),
        CleanupTarget("debug_*.py", "Debug utilities"),
        CleanupTarget("debug_graphql*.backup", "GraphQL debug backups"),
        CleanupTarget("verify_no_graphql.py", "GraphQL verification helper"),
        CleanupTarget("week12_analysis.log", "Week 12 analysis log"),
        CleanupTarget("week13_comprehensive_analysis.log", "Week 13 analysis log"),
    ),
    "low": (
        CleanupTarget("deployment", "Deployment scaffolding (unused)"),
        CleanupTarget("monitoring", "Monitoring scaffolding (unused)"),
        CleanupTarget("mcp_servers", "Local MCP server experiments"),
        CleanupTarget("models", "Redundant root-level models"),
        CleanupTarget("memory", "Cached conversation memory"),
        CleanupTarget("misc", "Miscellaneous throwaway assets"),
        CleanupTarget("node_helpers", "Legacy Node helper scripts"),
        CleanupTarget("quality_assurance", "Legacy QA automation"),
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean up non-essential Script Ohio 2.0 artifacts."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete the files/directories (default is dry-run).",
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=sorted(REMOVAL_GROUPS.keys()),
        default=sorted(REMOVAL_GROUPS.keys()),
        help="Limit cleanup to specific priority categories.",
    )
    parser.add_argument(
        "--list-targets",
        action="store_true",
        help="Only list the configured targets without globbing or deleting.",
    )
    return parser.parse_args()


def ensure_within_repo(path: Path) -> None:
    try:
        path.resolve().relative_to(REPO_ROOT)
    except ValueError as exc:  # pragma: no cover - defensive
        raise RuntimeError(f"Refusing to operate outside repo root: {path}") from exc


def enumerate_targets(
    categories: Iterable[str],
) -> list[tuple[CleanupTarget, Path | None]]:
    matches: list[tuple[CleanupTarget, Path | None]] = []
    for category in categories:
        for target in REMOVAL_GROUPS[category]:
            glob_match = sorted(REPO_ROOT.glob(target.pattern))
            if not glob_match:
                matches.append((target, None))
                continue
            for path in glob_match:
                ensure_within_repo(path)
                matches.append((target, path))
    return matches


def format_relative(path: Path | None) -> str:
    if path is None:
        return "(absent)"
    return str(path.relative_to(REPO_ROOT))


def delete_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def main() -> int:
    args = parse_args()
    if args.list_targets:
        print("Configured cleanup targets:")
        for category in args.categories:
            print(f"- {category.upper()} priority:")
            for target in REMOVAL_GROUPS[category]:
                print(f"  • {target.pattern} — {target.description}")
        return 0

    matches = enumerate_targets(args.categories)
    actionable = [(target, path) for target, path in matches if path]

    if not actionable:
        print("No matching files or directories found for the selected categories.")
        return 0

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[{mode}] {len(actionable)} targets identified.")

    for target, path in actionable:
        rel_path = format_relative(path)
        if args.apply:
            delete_path(path)
            print(f"Deleted {rel_path} ({target.description})")
        else:
            print(f"Would delete {rel_path} ({target.description})")

    absent_targets = [target for target, path in matches if path is None]
    if absent_targets:
        print("\nMissing targets (nothing to remove):")
        for target in absent_targets:
            print(f"- {target.pattern} ({target.description})")

    if not args.apply:
        print("\nDry run complete. Re-run with --apply to delete the listed targets.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

