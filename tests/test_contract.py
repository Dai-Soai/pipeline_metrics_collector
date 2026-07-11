from pipeline_metrics_collector.contract import (
    MetricRecord,
    MetricsReport,
    MetricsSource,
    MetricsSummary,
    metric_record_from_dict,
    metric_record_to_dict,
    metrics_report_from_dict,
    metrics_report_to_dict,
    metrics_source_from_dict,
    metrics_source_to_dict,
    metrics_summary_from_dict,
    metrics_summary_to_dict,
)


def test_metric_record_to_dict():
    record = MetricRecord(
        name="execution_completed_total",
        value=4,
        unit="count",
        category="execution",
        labels={"pipeline_id": "pipeline-demo"},
    )

    data = metric_record_to_dict(record)

    assert data == {
        "name": "execution_completed_total",
        "value": 4,
        "unit": "count",
        "category": "execution",
        "labels": {
            "pipeline_id": "pipeline-demo",
        },
    }


def test_metric_record_from_dict_uses_defaults():
    record = metric_record_from_dict(
        {
            "name": "event_total",
            "value": 5,
        }
    )

    assert record.name == "event_total"
    assert record.value == 5
    assert record.unit == "count"
    assert record.category == "runtime"
    assert record.labels == {}


def test_metrics_source_to_dict():
    source = MetricsSource(
        source_type="runtime_event_log",
        path="data/runtime_events.jsonl",
        exists=True,
        size_bytes=1268,
        metadata={"format": "jsonl"},
    )

    data = metrics_source_to_dict(source)

    assert data["source_type"] == "runtime_event_log"
    assert data["exists"] is True
    assert data["size_bytes"] == 1268
    assert data["metadata"]["format"] == "jsonl"


def test_metrics_source_from_dict_uses_defaults():
    source = metrics_source_from_dict(
        {
            "source_type": "consumer_report",
            "path": "data/consumer_report.json",
            "exists": False,
        }
    )

    assert source.source_type == "consumer_report"
    assert source.path == "data/consumer_report.json"
    assert source.exists is False
    assert source.size_bytes == 0
    assert source.metadata == {}


def test_metrics_summary_to_dict():
    summary = MetricsSummary(
        event_count=5,
        artifact_count=2,
        execution_requested=1,
        execution_completed=1,
        runtime_failed=0,
        accepted_events=3,
        rejected_events=2,
        acceptance_rate=0.6,
    )

    data = metrics_summary_to_dict(summary)

    assert data["event_count"] == 5
    assert data["artifact_count"] == 2
    assert data["execution_completed"] == 1
    assert data["accepted_events"] == 3
    assert data["acceptance_rate"] == 0.6


def test_metrics_summary_from_dict_uses_defaults():
    summary = metrics_summary_from_dict(
        {
            "event_count": 7,
            "execution_completed": 2,
        }
    )

    assert summary.event_count == 7
    assert summary.execution_completed == 2
    assert summary.artifact_count == 0
    assert summary.runtime_failed == 0
    assert summary.acceptance_rate == 0.0


def test_metrics_report_to_dict():
    report = MetricsReport(
        report_version="1.0",
        collector_version="0.1.0",
        run_id="run-001",
        generated_at="2026-07-11T06:00:00+00:00",
        status="completed",
        sources=[
            MetricsSource(
                source_type="runtime_event_log",
                path="data/runtime_events.jsonl",
                exists=True,
                size_bytes=1268,
            )
        ],
        summary=MetricsSummary(
            event_count=5,
            execution_completed=1,
        ),
        metrics=[
            MetricRecord(
                name="event_total",
                value=5,
            )
        ],
        warnings=["Consumer report not provided"],
    )

    data = metrics_report_to_dict(report)

    assert data["report_version"] == "1.0"
    assert data["run_id"] == "run-001"
    assert data["status"] == "completed"
    assert data["sources"][0]["source_type"] == "runtime_event_log"
    assert data["summary"]["event_count"] == 5
    assert data["metrics"][0]["name"] == "event_total"
    assert data["warnings"] == ["Consumer report not provided"]


def test_metrics_report_from_dict():
    report = metrics_report_from_dict(
        {
            "report_version": "1.0",
            "run_id": "run-002",
            "generated_at": "2026-07-11T06:05:00+00:00",
            "status": "partial",
            "sources": [
                {
                    "source_type": "consumer_report",
                    "path": "data/consumer_report.json",
                    "exists": True,
                    "size_bytes": 2048,
                }
            ],
            "summary": {
                "accepted_events": 4,
                "rejected_events": 1,
                "acceptance_rate": 0.8,
            },
            "metrics": [
                {
                    "name": "accepted_events_total",
                    "value": 4,
                    "category": "consumer",
                }
            ],
            "warnings": [],
        }
    )

    assert report.report_version == "1.0"
    assert report.run_id == "run-002"
    assert report.status == "partial"
    assert len(report.sources) == 1
    assert report.sources[0].size_bytes == 2048
    assert report.summary.accepted_events == 4
    assert report.summary.acceptance_rate == 0.8
    assert report.metrics[0].category == "consumer"
    assert report.warnings == []


def test_metrics_report_preserves_collector_version():
    report = MetricsReport(
        report_version="1.0",
        collector_version="0.1.0",
        run_id="run-001",
        generated_at="2026-07-11T07:00:00+00:00",
        status="completed",
    )

    payload = metrics_report_to_dict(report)
    loaded = metrics_report_from_dict(payload)

    assert payload["collector_version"] == "0.1.0"
    assert loaded.collector_version == "0.1.0"


def test_metrics_report_from_dict_supports_legacy_report():
    payload = {
        "report_version": "1.0",
        "run_id": "legacy-run",
        "generated_at": "2026-07-11T07:00:00+00:00",
        "status": "completed",
        "sources": [],
        "summary": {},
        "metrics": [],
        "warnings": [],
    }

    report = metrics_report_from_dict(payload)

    assert report.collector_version == "unknown"
