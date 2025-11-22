# CFBD Observability KPI Plan

## Overview
Track ingestion health across REST + GraphQL workloads so prediction runs stay reliable. Metrics feed Prometheus → Grafana dashboards and PagerDuty alerts.

## Core KPIs / SLIs
| KPI | Definition | Target / SLO | Instrumentation |
| --- | --- | --- | --- |
| API availability | % of CFBD calls returning 2xx after retries | ≥ 99.5% daily | `CFBDClient` telemetry counters exported via metrics hook |
| Latency P95 | P95 of client request latency (ms) | < 400 ms | `latency_ms` field emitted per request |
| Rate-limit breaches | # of 429 responses per hour | 0 sustained > 5 min | Telemetry event outcome == `rate_limit` |
| Dataset freshness | Age of latest row per dataset | < 15 min in-season | Compare ingest timestamps vs current time in ETL monitor |
| Schema drift MTTA | Time to acknowledge schema diff | < 12 h | `cfbd_schema_diff.py` job writes diff log; alert when entry appears |
| Incident MTTR | Time from alert to resolution | < 60 min | PagerDuty incident timeline |

## Dashboards
- **CFBD Client Overview** – total requests, success %, retry counts, rate-limit hits (Grafana).
- **Dataset Freshness** – per dataset lag charts (games, weather, predicted_points, etc.).
- **Schema Diff Feed** – Table of recent diff log entries with status (acknowledged / resolved).

## Alert Rules
- Error rate >0.5% over 5 min → page SRE.
- More than 3 rate-limit events in 5 min → notify data platform + auto-throttle non-critical agents.
- Freshness lag >30 min for any dataset during season → warn analytics lead.
- No schema snapshot posted in >24h → reminder to CI pipeline owners.

## Data Collection Steps
1. **CFBDClient Telemetry** – Use `telemetry_hook` or `metrics_log_path` to publish JSON, then scrape via sidecar to Prometheus.
2. **GraphQL Metrics** – Mirror same hook for `GraphQLClient` (latency, error counts).
3. **Freshness Probes** – After each ingest job, write timestamp to Redis/DB for dashboard queries.
4. **Schema Diff Alerts** – GitHub Action runs `cfbd_schema_diff.py`; diff output piped to Slack + log file.

## Review Cadence
- Weekly KPI review with Analytics + SRE (30 min).
- Monthly trend analysis for latency + error rates; adjust throttling if needed.
- Quarterly audit of alert thresholds and metric coverage.

