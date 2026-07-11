import json

from pipeline_metrics_collector.collector import MetricsCollection
from pipeline_metrics_collector.contract import (
    MetricRecord,
    MetricsSource,
    MetricsSummary,
)
from pipeline_metrics_collector.report import (
    METRICS_REPORT_FILENAME,
    build_metrics_report,
    build_metrics_report_inspection,
    get_metrics_report_path,
    read_metrics_report,
    validate_metrics_report_data,
    write_metrics_report,
)


def make_collection() -> MetricsCollection:
    return MetricsCollection(
        sources=[
            MetricsSource(
                source_type="runtime_event_log",
                path="data/runtime_events.jsonl",
                exists=True,
                size_bytes=1024,
            )
        ],
        summary=MetricsSummary(
            event_count=5,
            artifact_count=2,
            execution_requested=1,
            execution_completed=1,
            accepted_events=3,
            rejected_events=2,
            acceptance_rate=0.6,
        ),
        metrics=[
            MetricRecord(
                name="event_total",
                value=5,
            ),
            MetricRecord(
                name="runtime_duration_ms",
                value=2500.0,
                unit="milliseconds",
            ),
        ],
        runtime_events=[
            {
                "event_type": "RuntimeStarted",
            }
        ],
    )


def test_build_metrics_report():
    report = build_metrics_report(
        collection=make_collection(),
        run_id="run-001",
    )

    assert report.report_version == "1.0"
    assert report.collector_version == "0.1.0"
    assert report.run_id == "run-001"
    assert report.status == "completed"
    assert report.generated_at
    assert report.summary.event_count == 5
    assert len(report.metrics) == 2


def test_build_metrics_report_returns_partial_status():
    collection = make_collection()
    collection.warnings.append("Consumer report was not provided")

    report = build_metrics_report(collection)

    assert report.status == "partial"
    assert len(report.warnings) == 1


def test_build_metrics_report_returns_empty_status():
    collection = MetricsCollection()

    report = build_metrics_report(collection)

    assert report.status == "empty"


def test_get_metrics_report_path(tmp_path):
    report_path = get_metrics_report_path(tmp_path / "output")

    assert report_path == (tmp_path / "output" / METRICS_REPORT_FILENAME)


def test_write_and_read_metrics_report(tmp_path):
    report = build_metrics_report(
        collection=make_collection(),
        run_id="run-write-001",
    )

    report_path = write_metrics_report(
        report=report,
        output_dir=tmp_path / "output",
    )

    loaded = read_metrics_report(report_path)

    assert report_path.exists()
    assert loaded.run_id == "run-write-001"
    assert loaded.summary.event_count == 5
    assert loaded.metrics[0].name == "event_total"


def test_validate_metrics_report_data_accepts_valid_report():
    report = build_metrics_report(
        collection=make_collection(),
    )

    payload = {
        "report_version": report.report_version,
        "collector_version": report.collector_version,
        "run_id": report.run_id,
        "generated_at": report.generated_at,
        "status": report.status,
        "sources": [],
        "summary": {},
        "metrics": [
            {
                "name": "event_total",
                "value": 5,
            }
        ],
        "warnings": [],
    }

    assert validate_metrics_report_data(payload) == []


def test_validate_metrics_report_data_reports_missing_fields():
    errors = validate_metrics_report_data(
        {
            "status": "completed",
        }
    )

    assert any("report_version" in error for error in errors)
    assert any("metrics" in error for error in errors)


def test_validate_metrics_report_data_validates_metrics():
    payload = {
        "report_version": "1.0",
        "collector_version": "0.1.0",
        "run_id": "run-001",
        "generated_at": "2026-07-11T06:00:00+00:00",
        "status": "completed",
        "sources": [],
        "summary": {},
        "metrics": [
            {
                "value": 5,
            },
            "invalid",
        ],
        "warnings": [],
    }

    errors = validate_metrics_report_data(payload)

    assert any("missing name" in error for error in errors)
    assert any("must be an object" in error for error in errors)


def test_build_metrics_report_inspection():
    report = build_metrics_report(
        collection=make_collection(),
        run_id="run-inspect-001",
    )

    inspection = build_metrics_report_inspection(report)

    assert inspection["run_id"] == "run-inspect-001"
    assert inspection["collector_version"] == "0.1.0"
    assert inspection["status"] == "completed"
    assert inspection["source_count"] == 1
    assert inspection["metric_count"] == 2
    assert inspection["warning_count"] == 0
    assert inspection["summary"]["event_count"] == 5


def test_validate_metrics_report_requires_collector_version():
    report = build_metrics_report(
        collection=make_collection(),
    )

    payload = {
        "report_version": report.report_version,
        "run_id": report.run_id,
        "generated_at": report.generated_at,
        "status": report.status,
        "sources": [],
        "summary": {},
        "metrics": [],
        "warnings": [],
    }

    errors = validate_metrics_report_data(payload)

    assert "Missing required field: collector_version" in errors


def test_validate_metrics_report_rejects_invalid_collector_version():
    report = build_metrics_report(
        collection=make_collection(),
    )

    payload = {
        "report_version": report.report_version,
        "collector_version": 100,
        "run_id": report.run_id,
        "generated_at": report.generated_at,
        "status": report.status,
        "sources": [],
        "summary": {},
        "metrics": [],
        "warnings": [],
    }

    errors = validate_metrics_report_data(payload)

    assert "collector_version must be a string" in errors
