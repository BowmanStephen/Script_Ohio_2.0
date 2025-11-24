## Observability and Error Taxonomy

The agent platform now exposes a single observability surface under
`src/observability/`.  It provides three key features:

1. **Structured logging (`logging_config.py`)**
   - JSON output with `timestamp`, `service`, `environment`, and arbitrary
     `extra` fields.
   - `configure_logging` reads `SERVICE_NAME`, `APP_ENV`, `LOG_LEVEL`,
     and `STRUCTURED_LOGGING`.
   - Use `get_logger(__name__, component="workflow", service_name="agents")`
     to bind static context.

2. **Unified error taxonomy (`error_taxonomy.py`)**
   - `ErrorCategory` and `ErrorSeverity` enumerate every failure mode the
     orchestration layer understands (network, model, timeout, etc.).
   - `ErrorReport` captures normalized metadata for telemetry or runbooks.
   - `build_error_event()` and `summarize_exception()` make it easy to emit
     consistent payloads from scripts.

3. **In-process event hub (`hub.py`)**
   - Lightweight emitter that fans structured events to logs today and is
     ready for future OTLP/export integrations.
   - `ObservabilityHub.instance().emit_event("weekly_run", {...})`
     standardizes health signals, while `emit_error()` bridges directly from
     `ErrorReport` objects.

### How to instrument new code

1. Import once near the top of a module:
   ```python
   from src.observability import (
       ObservabilityHub,
       ErrorCategory,
       ErrorSeverity,
       get_logger,
   )

   logger = get_logger(__name__, component="weekly_pipeline")
   hub = ObservabilityHub.instance()
   ```

2. Emit structured events instead of ad-hoc prints:
   ```python
   hub.emit_event(
       "weekly_pipeline.step_completed",
       {"step": "feature_engineering", "duration_s": 42},
       severity=ErrorSeverity.INFO.value,
   )
   ```

3. When handling exceptions, wrap them into `ErrorReport` so downstream
   dashboards and alerts receive the correct category/severity.

### Metrics and dashboards

| Signal                         | Source                                  |
| ------------------------------ | --------------------------------------- |
| Agent lifecycle + durations   | `ObservabilityHub.emit_event` hooks     |
| Error inventories             | `ErrorHandler.error_stats`              |
| Weekly pipeline SLA tracking  | Runbook scripts emit `weekly_pipeline.*` |

All JSON logs remain newline-delimited for ingestion by OpenSearch, Loki,
or CloudWatch.  To ship them externally, configure the runtime to redirect
stdout to your collector of choice; no code changes are required.

