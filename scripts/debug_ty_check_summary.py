#!/usr/bin/env python3
"""Run ty and emit a small NDJSON summary for debug-mode workflows."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from collections import Counter
from pathlib import Path
from typing import Any


DEBUG_LOG_PATH = Path(__file__).resolve().parents[1] / ".cursor" / "debug.log"


def _append_ndjson(payload: dict[str, Any]) -> None:
    DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DEBUG_LOG_PATH.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n")


def _extract_error_locations(output: str, rule_prefix: str) -> Counter[str]:
    # Example header line:
    # error[invalid-assignment]: ...
    #    --> agents/core/advanced_coordination.py:1116:17
    header = re.compile(rf"^error\[{re.escape(rule_prefix)}[^\]]*\]:", re.MULTILINE)
    loc = re.compile(r"^\s*-->\s+(?P<path>[^:]+):\d+:\d+\s*$", re.MULTILINE)

    counts: Counter[str] = Counter()
    idx = 0
    while True:
        m = header.search(output, idx)
        if not m:
            break
        loc_m = loc.search(output, m.end())
        if loc_m:
            counts[loc_m.group("path")] += 1
            idx = loc_m.end()
        else:
            idx = m.end()
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default="baseline")
    args = parser.parse_args()

    run_id = str(args.run_id)
    cmd = ["uvx", "ty", "check", "agents/", "src/", "scripts/"]
    started = time.time()

    # region agent log
    _append_ndjson(
        {
            "sessionId": "debug-session",
            "runId": run_id,
            "hypothesisId": "H0",
            "location": "scripts/debug_ty_check_summary.py:main:start",
            "message": "ty check start",
            "data": {"cmd": cmd},
            "timestamp": int(time.time() * 1000),
        }
    )
    # endregion agent log

    proc = subprocess.run(cmd, capture_output=True, text=True)
    duration_ms = int((time.time() - started) * 1000)
    combined = (proc.stdout or "") + (proc.stderr or "")

    # region agent log
    _append_ndjson(
        {
            "sessionId": "debug-session",
            "runId": run_id,
            "hypothesisId": "H0",
            "location": "scripts/debug_ty_check_summary.py:main:completed",
            "message": "ty check completed",
            "data": {
                "returncode": proc.returncode,
                "duration_ms": duration_ms,
                "stdout_chars": len(proc.stdout or ""),
                "stderr_chars": len(proc.stderr or ""),
            },
            "timestamp": int(time.time() * 1000),
        }
    )
    # endregion agent log

    invalid_assignment_by_file = _extract_error_locations(combined, "invalid-assignment")
    invalid_argument_by_file = _extract_error_locations(combined, "invalid-argument")

    # region agent log
    _append_ndjson(
        {
            "sessionId": "debug-session",
            "runId": run_id,
            "hypothesisId": "H1",
            "location": "scripts/debug_ty_check_summary.py:main:summary",
            "message": "ty error summary",
            "data": {
                "invalid_assignment_total": int(sum(invalid_assignment_by_file.values())),
                "invalid_argument_total": int(sum(invalid_argument_by_file.values())),
                "invalid_assignment_top_files": invalid_assignment_by_file.most_common(8),
                "invalid_argument_top_files": invalid_argument_by_file.most_common(8),
            },
            "timestamp": int(time.time() * 1000),
        }
    )
    # endregion agent log

    # region agent log
    _append_ndjson(
        {
            "sessionId": "debug-session",
            "runId": run_id,
            "hypothesisId": "H0",
            "location": "scripts/debug_ty_check_summary.py:main:end",
            "message": "debug summary written",
            "data": {"debug_log_path": str(DEBUG_LOG_PATH)},
            "timestamp": int(time.time() * 1000),
        }
    )
    # endregion agent log

    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
