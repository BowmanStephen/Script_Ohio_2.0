"""Utility to compare CFBD dataset schemas against a stored baseline."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from cfbd_client import CFBDClient
from cfbd_client.datasets import (
    fetch_games,
    fetch_lines,
    fetch_media,
    fetch_predicted_points,
    fetch_ratings,
    fetch_recruiting,
    fetch_weather,
)

BASELINE_PATH = Path("project_management/cfbd_schema_baseline.json")
DEFAULT_SNAPSHOT_DIR = Path("logs/cfbd_schema")

DATASET_FUNCS: Tuple[Tuple[str, Any, Dict[str, Any]], ...] = (
    ("games", fetch_games, {"year": 2025, "week": 1}),
    ("ratings", fetch_ratings, {"year": 2025, "week": 1}),
    ("lines", fetch_lines, {"year": 2025, "week": 1}),
    ("recruiting", fetch_recruiting, {"year": 2025}),
    ("weather", fetch_weather, {"year": 2025, "week": 1}),
    ("media", fetch_media, {"year": 2025, "week": 1}),
    ("predicted_points", fetch_predicted_points, {"year": 2025, "week": 1}),
)


def snapshot_schemas(client: CFBDClient) -> Dict[str, List[str]]:
    schemas: Dict[str, List[str]] = {}
    for name, func, kwargs in DATASET_FUNCS:
        try:
            df = func(client, **kwargs)
            schemas[name] = sorted(df.columns.tolist())
        except Exception as exc:  # pragma: no cover - network dependent
            schemas[name] = [f"error: {exc}"]
    return schemas


def compare_to_baseline(current: Dict[str, List[str]]) -> Dict[str, Dict[str, List[str]]]:
    if BASELINE_PATH.exists():
        baseline = json.loads(BASELINE_PATH.read_text())
    else:
        baseline = {}

    diffs: Dict[str, Dict[str, List[str]]] = {}
    for name, columns in current.items():
        if any(col.startswith("error:") for col in columns):
            continue
        baseline_cols = set(baseline.get(name, []))
        current_cols = set(columns)
        added = sorted(current_cols - baseline_cols)
        removed = sorted(baseline_cols - current_cols)
        if added or removed:
            diffs[name] = {"added": added, "removed": removed}
    return diffs


def write_snapshot(schemas: Dict[str, List[str]], snapshot_dir: Path) -> Path:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot_path = snapshot_dir / f"cfbd_schema_snapshot_{timestamp}.json"
    snapshot_path.write_text(json.dumps(schemas, indent=2))
    return snapshot_path


def append_diff_log(diffs: Dict[str, Dict[str, List[str]]], log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "diffs": diffs,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare CFBD schemas with baseline")
    parser.add_argument("--snapshot-dir", default=DEFAULT_SNAPSHOT_DIR, help="Where to store schema snapshots")
    parser.add_argument("--log", default="logs/cfbd_schema/diff.log", help="Diff log file path")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with non-zero code when schema differences are detected.",
    )
    args = parser.parse_args()

    client = CFBDClient()
    schemas = snapshot_schemas(client)
    snapshot_path = write_snapshot(schemas, Path(args.snapshot_dir))
    diffs = compare_to_baseline(schemas)
    append_diff_log(diffs, Path(args.log))
    print(f"Schema snapshot written to {snapshot_path}")
    if diffs:
        print("Differences detected:")
        for dataset, delta in diffs.items():
            print(f"- {dataset}: +{delta['added']}, -{delta['removed']}")
        if args.check:
            print("CFBD schema changes detected. Update baseline or investigate before merging.")
            sys.exit(1)
    else:
        print("No schema differences detected.")


if __name__ == "__main__":  # pragma: no cover
    main()
