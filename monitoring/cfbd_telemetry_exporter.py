"""Expose CFBD telemetry JSON logs as Prometheus metrics."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Dict

from prometheus_client import Counter, Gauge, Histogram, start_http_server

REQUEST_COUNTER = Counter(
    "cfbd_client_requests_total",
    "Total CFBD client requests by outcome",
    ["client", "outcome"],
)
LATENCY_HIST = Histogram(
    "cfbd_client_latency_ms",
    "Latency distribution for CFBD client requests",
    buckets=(10, 25, 50, 100, 250, 500, 1000, 2000, 4000),
)
RETRY_COUNTER = Counter(
    "cfbd_client_retries_total",
    "Number of retries performed by CFBD client",
    ["client"],
)
SUBSCRIPTION_HEARTBEAT = Gauge(
    "cfbd_subscription_last_heartbeat",
    "Unix timestamp of last GraphQL subscription event",
)


def process_line(line: str) -> None:
    try:
        payload: Dict[str, object] = json.loads(line)
    except json.JSONDecodeError:
        return

    client = str(payload.get("client", "rest"))
    outcome = str(payload.get("outcome", "unknown"))
    REQUEST_COUNTER.labels(client=client, outcome=outcome).inc()

    latency_ms = payload.get("latency_ms")
    if isinstance(latency_ms, (int, float)):
        LATENCY_HIST.observe(latency_ms)

    retries = payload.get("retry_count")
    if isinstance(retries, (int, float)) and retries > 0:
        RETRY_COUNTER.labels(client=client).inc(retries)

    if outcome == "subscription_event":
        SUBSCRIPTION_HEARTBEAT.set(time.time())


def tail_file(path: Path, poll_interval: float = 1.0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        handle.seek(0, 2)
        while True:
            line = handle.readline()
            if not line:
                time.sleep(poll_interval)
                continue
            process_line(line)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CFBD telemetry exporter")
    parser.add_argument("--log-file", default="logs/cfbd_events.jsonl", help="Telemetry log file path")
    parser.add_argument("--port", type=int, default=9107, help="Prometheus metrics port")
    parser.add_argument("--poll", type=float, default=1.0, help="Polling interval for file tailing")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    start_http_server(args.port)
    path = Path(args.log_file)
    tail_file(path, poll_interval=args.poll)


if __name__ == "__main__":
    main()
