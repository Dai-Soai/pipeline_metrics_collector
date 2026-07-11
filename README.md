# Pipeline Metrics Collector MVP

Utility #26 for RADAR_SERVICE.

Pipeline Metrics Collector reads runtime artifacts produced by reusable pipeline utilities and generates a normalized JSON metrics report.

## Purpose

The utility provides a reusable metrics collection layer for RADAR_SERVICE pipelines.

It collects metrics from:

- runtime event logs
- runtime reports
- consumer reports

It produces a normalized metrics report that can later be consumed by:

- dashboards
- monitoring utilities
- health checks
- alert systems
- exporters
- runtime inspection tools

## Features

- Metrics contract
- Runtime event metrics
- Artifact metrics
- Execution metrics
- Consumer metrics
- Latency and duration metrics
- Multi-source metrics collection
- JSON metrics report
- Report inspection
- Report validation
- Collector version metadata
- CLI workflow
- Pytest coverage

## Architecture

```text
Runtime Event Log
        │
        ├── Runtime Report
        │
        └── Consumer Report
                │
                ▼
         Source Loader
                │
                ▼
        Metrics Builders
                │
        ┌───────┼────────┐
        │       │        │
     Runtime  Consumer  Latency
     Metrics  Metrics   Metrics
        │       │        │
        └───────┼────────┘
                ▼
       Metrics Collector Engine
                │
                ▼
       pipeline_metrics.json
 ```

## Project Structure

pipeline_metrics_collector/
├── src/
│   └── pipeline_metrics_collector/
│       ├── __init__.py
│       ├── cli.py
│       ├── collector.py
│       ├── contract.py
│       ├── latency.py
│       ├── loader.py
│       ├── metrics.py
│       ├── report.py
│       └── version.py
├── tests/
│   ├── test_cli.py
│   ├── test_collector.py
│   ├── test_contract.py
│   ├── test_latency.py
│   ├── test_loader.py
│   ├── test_metrics.py
│   └── test_report.py
├── data/
│   └── output/
├── pyproject.toml
├── README.md
└── .gitignore

## Installation

Create and activate a virtual environment:

python3 -m venv .venv
source .venv/bin/activate

Install the package in editable mode:

pip install -e .

Install development dependencies:

pip install pytest build

## CLI

Show help:

pipeline-metrics --help

### Collect metrics

pipeline-metrics collect \
  --event-log ../pipeline_runtime_bridge/data/runtime_demo/runtime_events.jsonl \
  --runtime-report ../pipeline_runtime_bridge/data/runtime_demo/output/runtime_report.json \
  --consumer-report ../pipeline_runtime_consumer/data/output/consumer_report.json \
  --output-dir data/output

Generated report:

data/output/pipeline_metrics.json

## Inspect report

pipeline-metrics inspect \
  --report data/output/pipeline_metrics.json

## Validate report

pipeline-metrics validate \
  --report data/output/pipeline_metrics.json

## Metrics Categories

The generated report may contain metrics from the following categories:

- runtime
- event
- artifact
- execution
- consumer
- latency

Example metrics:

event_total
runtime_started_total
runtime_failed_total
artifact_registered_total
artifact_routed_total
execution_requested_total
execution_completed_total
execution_success_total
execution_failure_total
consumer_processed_events
consumer_accepted_events
consumer_rejected_events
consumer_acceptance_rate
average_execution_latency_ms
minimum_execution_latency_ms
maximum_execution_latency_ms
runtime_duration_ms

## Report Contract

The top-level JSON report contains:

{
  "report_version": "1.0",
  "collector_version": "0.1.0",
  "run_id": "generated-run-id",
  "generated_at": "UTC timestamp",
  "status": "completed",
  "sources": [],
  "summary": {},
  "metrics": [],
  "warnings": []
}

Version semantics:

report_version

Represents the JSON report schema version.

collector_version

Represents the Pipeline Metrics Collector software version.

## Testing

Run:

pytest

Current result:

97 passed

## Build

Clean previous artifacts:

rm -rf build dist *.egg-info

Build the package:

python -m build

Expected artifacts:

dist/pipeline_metrics_collector-0.1.0-py3-none-any.whl
dist/pipeline_metrics_collector-0.1.0.tar.gz

## Status

Utility: #26
Name: Pipeline Metrics Collector MVP
Version: v0.1.0
Status: RELEASE CANDIDATE

## License

MIT
