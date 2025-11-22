# CFBD Data Governance & Agent Onboarding

## Purpose
Define how CFBD schemas enter production, how agents gain access, and how incidents are triaged so real-time analytics stay compliant with API terms.

## Roles
- **Data Platform Lead** – approves schema changes, owns baseline (`project_management/cfbd_schema_baseline.json`).
- **Agent Steward** – ensures each new agent inherits `CFBDClient` and meets telemetry standards.
- **SRE On-call** – monitors rate limits, handles escalations to CFBD support.

## Schema Change Workflow
1. **Detect** – Nightly `python project_management/cfbd_schema_diff.py` snapshot runs in CI.
2. **Review** – If diff logged, Data Platform Lead validates fields against docs (GraphQL + REST) and updates baseline after sign-off.
3. **Implement** – Affected dataset helpers/tests updated in same PR as baseline change.
4. **Communicate** – Post summary in `#cfbd-changes` with link to PR and impacted agents.

## Agent Onboarding Checklist
- [ ] Uses `CFBDClient`/`GraphQLClient` (no ad-hoc requests).
- [ ] Rate-limit + retry logic verified via tests.
- [ ] Telemetry hook wired into orchestrator metrics store.
- [ ] Access key loaded from env/secret manager; no hard-coded credentials.
- [ ] Dataset schemas referenced from baseline file.
- [ ] Incident run-book links included in agent README block.

## Incident Response
1. **Alerting** – Grafana alerts for >0.5% API error rate or sustained 429s ping PagerDuty `cfbd-ingestion`.
2. **Triage** – SRE confirms status page + logs; if CFBD outage, update status channel.
3. **Mitigation** – Pause non-essential agents (predictions) before ingest to stay under limit.
4. **Postmortem** – Within 24h, document root cause, fix, and action items in `project_management/incidents/`.

## Access Governance
- Quarterly review of `CFBD_API_KEY` usage per agent; remove stale service accounts.
- Keys stored in 1Password/Secrets Manager with rotation every 90 days.
- Notebook users must load keys via `%env CFBD_API_KEY` rather than embedding in notebooks.

## Documentation & Audit
- Keep run-book (`docs/CFBD_RUNBOOK.md`) updated monthly or after major change.
- Archive schema diff logs (`logs/cfbd_schema/diff.log`) for 6 months for compliance evidence.
- Track agent onboarding approvals in `project_management/CFBD_GOVERNANCE.md` appendix (future section).

## Automation & CI
- `.github/workflows/cfbd-governance.yml` runs on every PR/push to enforce schema checks.
- `python project_management/cfbd_schema_diff.py --check` snapshots REST schemas and fails on unapproved diffs.
- `python project_management/automation/check_cfbd_clients.py` ensures agents rely on the shared `CFBDClient`/`GraphQLClient` wrappers rather than raw `requests`.
