Dashboard JSON definitions go here.

Not built in this pass - the metrics they'd visualize now exist
(app/core/metrics.py, scraped per monitoring/prometheus/prometheus.yml),
but authoring the dashboard JSON itself is lower-value to hand-write than
to build directly in the Grafana UI against live data, then export.
Suggested starting panels: jobs_submitted_total vs jobs_completed_total
(by outcome), job_processing_duration_seconds (p50/p95/p99), job_retries_total
by error_code, and api_request_duration_seconds by path.
