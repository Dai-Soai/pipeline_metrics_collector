# Pipeline Metrics Collector MVP

Utility #26 for RADAR_SERVICE.

## Purpose

Pipeline Metrics Collector reads runtime events, runtime reports and consumer reports, then produces structured execution and operational metrics.

## MVP Scope

- Metrics contract
- Runtime event loader
- Runtime report loader
- Consumer report loader
- Runtime event counters
- Consumer metrics
- Execution latency metrics
- Metrics collector engine
- JSON metrics report
- CLI-first workflow

## Runtime Relationship

```text
Pipeline Runtime Bridge
        │
        ├── runtime_events.jsonl
        └── runtime_report.json
                 │
                 ▼
Pipeline Runtime Consumer
        │
        └── consumer_report.json
                 │
                 ▼
Pipeline Metrics Collector
        │
        └── pipeline_metrics.json
Status

M1 Bootstrap Project: in progress.
