from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class MetricRecord:
    name: str
    value: int | float
    unit: str = "count"
    category: str = "runtime"
    labels: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class MetricsSource:
    source_type: str
    path: str
    exists: bool
    size_bytes: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MetricsSummary:
    event_count: int = 0
    artifact_count: int = 0
    execution_requested: int = 0
    execution_completed: int = 0
    runtime_failed: int = 0
    accepted_events: int = 0
    rejected_events: int = 0
    acceptance_rate: float = 0.0


@dataclass(slots=True)
class MetricsReport:
    report_version: str
    run_id: str
    generated_at: str
    status: str
    sources: list[MetricsSource] = field(default_factory=list)
    summary: MetricsSummary = field(default_factory=MetricsSummary)
    metrics: list[MetricRecord] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def metric_record_to_dict(record: MetricRecord) -> dict[str, Any]:
    return asdict(record)


def metric_record_from_dict(data: dict[str, Any]) -> MetricRecord:
    return MetricRecord(
        name=data["name"],
        value=data["value"],
        unit=data.get("unit", "count"),
        category=data.get("category", "runtime"),
        labels=dict(data.get("labels", {})),
    )


def metrics_source_to_dict(source: MetricsSource) -> dict[str, Any]:
    return asdict(source)


def metrics_source_from_dict(data: dict[str, Any]) -> MetricsSource:
    return MetricsSource(
        source_type=data["source_type"],
        path=data["path"],
        exists=data["exists"],
        size_bytes=data.get("size_bytes", 0),
        metadata=dict(data.get("metadata", {})),
    )


def metrics_summary_to_dict(summary: MetricsSummary) -> dict[str, Any]:
    return asdict(summary)


def metrics_summary_from_dict(data: dict[str, Any]) -> MetricsSummary:
    return MetricsSummary(
        event_count=data.get("event_count", 0),
        artifact_count=data.get("artifact_count", 0),
        execution_requested=data.get("execution_requested", 0),
        execution_completed=data.get("execution_completed", 0),
        runtime_failed=data.get("runtime_failed", 0),
        accepted_events=data.get("accepted_events", 0),
        rejected_events=data.get("rejected_events", 0),
        acceptance_rate=data.get("acceptance_rate", 0.0),
    )


def metrics_report_to_dict(report: MetricsReport) -> dict[str, Any]:
    return {
        "report_version": report.report_version,
        "run_id": report.run_id,
        "generated_at": report.generated_at,
        "status": report.status,
        "sources": [
            metrics_source_to_dict(source)
            for source in report.sources
        ],
        "summary": metrics_summary_to_dict(report.summary),
        "metrics": [
            metric_record_to_dict(metric)
            for metric in report.metrics
        ],
        "warnings": list(report.warnings),
    }


def metrics_report_from_dict(data: dict[str, Any]) -> MetricsReport:
    return MetricsReport(
        report_version=data["report_version"],
        run_id=data["run_id"],
        generated_at=data["generated_at"],
        status=data["status"],
        sources=[
            metrics_source_from_dict(source)
            for source in data.get("sources", [])
        ],
        summary=metrics_summary_from_dict(
            data.get("summary", {})
        ),
        metrics=[
            metric_record_from_dict(metric)
            for metric in data.get("metrics", [])
        ],
        warnings=list(data.get("warnings", [])),
    )
