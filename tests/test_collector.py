import json

from pipeline_metrics_collector.collector import (
    MetricsCollection,
    collect_pipeline_metrics,
    collection_status,
    find_metric,
    get_runtime_artifact_count,
    load_optional_consumer_report,
    load_optional_runtime_report,
)


def write_event_log(path):
    records = [
        {
            "event_type": "RuntimeStarted",
            "payload": {
                "pipeline_id": "pipeline-demo",
            },
            "event_id": "event-001",
            "timestamp": "2026-07-11T06:00:00+00:00",
        },
        {
            "event_type": "ArtifactRegistered",
            "payload": {
                "artifact_id": "summary-001",
            },
            "event_id": "event-002",
            "timestamp": "2026-07-11T06:00:00.500000+00:00",
        },
        {
            "event_type": "ExecutionRequested",
            "payload": {
                "request_id": "request-001",
            },
            "event_id": "event-003",
            "timestamp": "2026-07-11T06:00:01+00:00",
        },
        {
            "event_type": "ExecutionCompleted",
            "payload": {
                "request_id": "request-001",
                "success": True,
            },
            "event_id": "event-004",
            "timestamp": "2026-07-11T06:00:02.500000+00:00",
        },
    ]

    path.write_text(
        "\n".join(
            json.dumps(record)
            for record in records
        )
        + "\n",
        encoding="utf-8",
    )


def write_runtime_report(path):
    path.write_text(
        json.dumps(
            {
                "status": "completed",
                "summary": {
                    "artifact_count": 2,
                    "event_count": 4,
                },
            }
        ),
        encoding="utf-8",
    )


def write_consumer_report(path):
    path.write_text(
        json.dumps(
            {
                "report_version": "1.0",
                "status": "completed",
                "subscription": {
                    "consumer_id": "runtime-observer",
                    "event_types": [
                        "RuntimeStarted",
                        "ExecutionCompleted",
                    ],
                    "enabled": True,
                },
                "summary": {
                    "processed_events": 4,
                    "accepted_events": 2,
                    "rejected_events": 2,
                    "result_count": 4,
                    "acceptance_rate": 0.5,
                },
            }
        ),
        encoding="utf-8",
    )


def test_get_runtime_artifact_count():
    report = {
        "summary": {
            "artifact_count": 3,
        }
    }

    assert get_runtime_artifact_count(report) == 3


def test_get_runtime_artifact_count_returns_zero_for_missing_data():
    assert get_runtime_artifact_count(None) == 0
    assert get_runtime_artifact_count({}) == 0
    assert get_runtime_artifact_count(
        {"summary": []}
    ) == 0


def test_load_optional_runtime_report_without_path():
    source, report, warnings = (
        load_optional_runtime_report(None)
    )

    assert source is None
    assert report is None
    assert warnings == [
        "Runtime report was not provided"
    ]


def test_load_optional_runtime_report_handles_missing_file(tmp_path):
    source, report, warnings = (
        load_optional_runtime_report(
            tmp_path / "missing.json"
        )
    )

    assert source is not None
    assert source.exists is False
    assert source.metadata["load_status"] == "failed"
    assert report is None
    assert warnings


def test_load_optional_consumer_report_without_path():
    source, report, warnings = (
        load_optional_consumer_report(None)
    )

    assert source is None
    assert report is None
    assert warnings == [
        "Consumer report was not provided"
    ]


def test_load_optional_consumer_report_handles_invalid_file(tmp_path):
    report_path = tmp_path / "consumer_report.json"
    report_path.write_text(
        "{invalid-json}",
        encoding="utf-8",
    )

    source, report, warnings = (
        load_optional_consumer_report(report_path)
    )

    assert source is not None
    assert source.exists is True
    assert source.metadata["load_status"] == "failed"
    assert report is None
    assert warnings


def test_collect_pipeline_metrics_with_all_sources(tmp_path):
    event_log = tmp_path / "runtime_events.jsonl"
    runtime_report = tmp_path / "runtime_report.json"
    consumer_report = tmp_path / "consumer_report.json"

    write_event_log(event_log)
    write_runtime_report(runtime_report)
    write_consumer_report(consumer_report)

    collection = collect_pipeline_metrics(
        event_log_path=event_log,
        runtime_report_path=runtime_report,
        consumer_report_path=consumer_report,
    )

    assert len(collection.sources) == 3
    assert len(collection.runtime_events) == 4
    assert collection.runtime_report is not None
    assert collection.consumer_report is not None

    assert collection.summary.event_count == 4
    assert collection.summary.artifact_count == 2
    assert collection.summary.execution_requested == 1
    assert collection.summary.execution_completed == 1
    assert collection.summary.accepted_events == 2
    assert collection.summary.rejected_events == 2
    assert collection.summary.acceptance_rate == 0.5

    assert collection.warnings == []


def test_collect_pipeline_metrics_builds_runtime_metrics(tmp_path):
    event_log = tmp_path / "runtime_events.jsonl"
    write_event_log(event_log)

    collection = collect_pipeline_metrics(
        event_log_path=event_log,
    )

    event_total = find_metric(
        collection,
        "event_total",
    )
    latency = find_metric(
        collection,
        "average_execution_latency_ms",
    )
    duration = find_metric(
        collection,
        "runtime_duration_ms",
    )

    assert event_total is not None
    assert event_total.value == 4

    assert latency is not None
    assert latency.value == 1500.0

    assert duration is not None
    assert duration.value == 2500.0


def test_collect_pipeline_metrics_builds_consumer_metrics(tmp_path):
    event_log = tmp_path / "runtime_events.jsonl"
    consumer_report = tmp_path / "consumer_report.json"

    write_event_log(event_log)
    write_consumer_report(consumer_report)

    collection = collect_pipeline_metrics(
        event_log_path=event_log,
        consumer_report_path=consumer_report,
    )

    accepted = find_metric(
        collection,
        "consumer_accepted_events",
    )
    rejected = find_metric(
        collection,
        "consumer_rejected_events",
    )

    assert accepted is not None
    assert accepted.value == 2

    assert rejected is not None
    assert rejected.value == 2


def test_collect_pipeline_metrics_handles_optional_sources(tmp_path):
    event_log = tmp_path / "runtime_events.jsonl"
    write_event_log(event_log)

    collection = collect_pipeline_metrics(
        event_log_path=event_log,
    )

    assert len(collection.sources) == 1
    assert collection.summary.event_count == 4
    assert len(collection.warnings) == 2
    assert "Runtime report was not provided" in (
        collection.warnings
    )
    assert "Consumer report was not provided" in (
        collection.warnings
    )


def test_collection_status_returns_completed():
    collection = MetricsCollection(
        runtime_events=[
            {
                "event_type": "RuntimeStarted",
            }
        ],
    )

    assert collection_status(collection) == "completed"


def test_collection_status_returns_empty():
    collection = MetricsCollection()

    assert collection_status(collection) == "empty"


def test_collection_status_returns_partial_for_warnings():
    collection = MetricsCollection(
        runtime_events=[
            {
                "event_type": "RuntimeStarted",
            }
        ],
        warnings=[
            "Consumer report was not provided",
        ],
    )

    assert collection_status(collection) == "partial"


def test_find_metric_returns_none_for_unknown_metric():
    collection = MetricsCollection()

    assert find_metric(
        collection,
        "unknown_metric",
    ) is None
