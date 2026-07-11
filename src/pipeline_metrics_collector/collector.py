from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pipeline_metrics_collector.contract import (
    MetricRecord,
    MetricsSource,
    MetricsSummary,
)
from pipeline_metrics_collector.latency import (
    build_latency_metric_records,
)
from pipeline_metrics_collector.loader import (
    build_metrics_source,
    load_consumer_report,
    load_runtime_events,
    load_runtime_report,
)
from pipeline_metrics_collector.metrics import (
    build_consumer_metric_records,
    build_consumer_metrics_summary,
    build_runtime_metric_records,
    build_runtime_metrics_summary,
)


@dataclass(slots=True)
class MetricsCollection:
    sources: list[MetricsSource] = field(default_factory=list)
    summary: MetricsSummary = field(default_factory=MetricsSummary)
    metrics: list[MetricRecord] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    runtime_events: list[dict[str, Any]] = field(default_factory=list)
    runtime_report: dict[str, Any] | None = None
    consumer_report: dict[str, Any] | None = None


def get_runtime_artifact_count(
    runtime_report: dict[str, Any] | None,
) -> int:
    if runtime_report is None:
        return 0

    summary = runtime_report.get("summary", {})

    if not isinstance(summary, dict):
        return 0

    value = summary.get("artifact_count", 0)

    if isinstance(value, bool):
        return 0

    if isinstance(value, int):
        return max(value, 0)

    return 0


def load_optional_runtime_report(
    path: str | Path | None,
) -> tuple[
    MetricsSource | None,
    dict[str, Any] | None,
    list[str],
]:
    if path is None:
        return (
            None,
            None,
            ["Runtime report was not provided"],
        )

    try:
        source, report = load_runtime_report(path)
    except (FileNotFoundError, ValueError) as exc:
        source = build_metrics_source(
            source_type="runtime_report",
            path=path,
            metadata={
                "load_status": "failed",
            },
        )

        return (
            source,
            None,
            [str(exc)],
        )

    return source, report, []


def load_optional_consumer_report(
    path: str | Path | None,
) -> tuple[
    MetricsSource | None,
    dict[str, Any] | None,
    list[str],
]:
    if path is None:
        return (
            None,
            None,
            ["Consumer report was not provided"],
        )

    try:
        source, report = load_consumer_report(path)
    except (FileNotFoundError, ValueError) as exc:
        source = build_metrics_source(
            source_type="consumer_report",
            path=path,
            metadata={
                "load_status": "failed",
            },
        )

        return (
            source,
            None,
            [str(exc)],
        )

    return source, report, []


def collect_pipeline_metrics(
    event_log_path: str | Path,
    runtime_report_path: str | Path | None = None,
    consumer_report_path: str | Path | None = None,
) -> MetricsCollection:
    event_source, runtime_events = load_runtime_events(
        event_log_path
    )

    sources: list[MetricsSource] = [
        event_source,
    ]
    warnings: list[str] = []

    runtime_source, runtime_report, runtime_warnings = (
        load_optional_runtime_report(runtime_report_path)
    )

    if runtime_source is not None:
        sources.append(runtime_source)

    warnings.extend(runtime_warnings)

    consumer_source, consumer_report, consumer_warnings = (
        load_optional_consumer_report(consumer_report_path)
    )

    if consumer_source is not None:
        sources.append(consumer_source)

    warnings.extend(consumer_warnings)

    artifact_count = get_runtime_artifact_count(
        runtime_report
    )

    summary = build_runtime_metrics_summary(
        events=runtime_events,
        artifact_count=artifact_count,
    )

    metrics = build_runtime_metric_records(
        runtime_events
    )

    latency_metrics, latency_warnings = (
        build_latency_metric_records(runtime_events)
    )

    metrics.extend(latency_metrics)
    warnings.extend(latency_warnings)

    if consumer_report is not None:
        summary = build_consumer_metrics_summary(
            consumer_report=consumer_report,
            base_summary=summary,
        )

        metrics.extend(
            build_consumer_metric_records(
                consumer_report
            )
        )

    return MetricsCollection(
        sources=sources,
        summary=summary,
        metrics=metrics,
        warnings=warnings,
        runtime_events=runtime_events,
        runtime_report=runtime_report,
        consumer_report=consumer_report,
    )


def collection_status(
    collection: MetricsCollection,
) -> str:
    if not collection.runtime_events:
        return "empty"

    failed_sources = [
        source
        for source in collection.sources
        if source.metadata.get("load_status") == "failed"
    ]

    if failed_sources or collection.warnings:
        return "partial"

    return "completed"


def find_metric(
    collection: MetricsCollection,
    name: str,
) -> MetricRecord | None:
    return next(
        (
            metric
            for metric in collection.metrics
            if metric.name == name
            and not metric.labels
        ),
        None,
    )
