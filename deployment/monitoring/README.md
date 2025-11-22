# CFBD KPI Monitoring Artifacts

This folder contains starter configuration for scraping telemetry emitted by the Script Ohio CFBD clients.

## Files
- `prometheus_scrape.yml` – add this job to your Prometheus configuration to scrape the lightweight `/metrics` exporter that ingests `telemetry_hook` JSON logs.
- `grafana_dashboard_cfbd.json` – import into Grafana to visualize availability, latency, rate-limit hits, and freshness KPIs outlined in `project_management/CFBD_KPI_PLAN.md`.
- `alert_rules.yml` – Alertmanager rules for API error rate, latency, freshness lag, and schema drift MTTA.

## Usage
1. Deploy the telemetry forwarder (sidecar) that converts log lines from `CFBDClient` / `GraphQLClient` into Prometheus metrics (`cfbd_client_requests_total`, `cfbd_client_latency_ms_bucket`, etc.).
2. Point Prometheus at the exporter using `prometheus_scrape.yml`.
3. Import the dashboard JSON and update datasource references.
4. Load the alert rules into Alertmanager, wiring PagerDuty/Slack routing keys.

Adjust namespace/job labels to match your deployment topology.
