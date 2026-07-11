from __future__ import annotations

from collections import Counter
from typing import Any

from pipeline_metrics_collector.contract import MetricRecord, MetricsSummary

RUNTIME_EVENT_TYPES = {
    "RuntimeStarted",
    "ArtifactRegistered",
    "ArtifactRouted",
    "ExecutionRequested",
    "ExecutionCompleted",
    "RuntimeFailed",
}


def get_event_type(
    event: dict[str, Any],
) -> str:
    event_type = event.get("event_type")

    if not isinstance(event_type, str) or not event_type.strip():
        return "Unknown"

    return event_type


def count_event_types(
    events: list[dict[str, Any]],
) -> dict[str, int]:
    counts = Counter(get_event_type(event) for event in events)

    return dict(counts)


def count_execution_outcomes(
    events: list[dict[str, Any]],
) -> dict[str, int]:
    success_total = 0
    failure_total = 0

    for event in events:
        if get_event_type(event) != "ExecutionCompleted":
            continue

        payload = event.get("payload", {})

        if not isinstance(payload, dict):
            failure_total += 1
            continue

        if payload.get("success") is True:
            success_total += 1
        else:
            failure_total += 1

    return {
        "execution_success_total": success_total,
        "execution_failure_total": failure_total,
    }


def build_runtime_metrics_summary(
    events: list[dict[str, Any]],
    artifact_count: int = 0,
) -> MetricsSummary:
    event_type_counts = count_event_types(events)

    return MetricsSummary(
        event_count=len(events),
        artifact_count=artifact_count,
        execution_requested=event_type_counts.get(
            "ExecutionRequested",
            0,
        ),
        execution_completed=event_type_counts.get(
            "ExecutionCompleted",
            0,
        ),
        runtime_failed=event_type_counts.get(
            "RuntimeFailed",
            0,
        ),
    )


def build_runtime_metric_records(
    events: list[dict[str, Any]],
) -> list[MetricRecord]:
    event_type_counts = count_event_types(events)
    execution_outcomes = count_execution_outcomes(events)

    metrics = [
        MetricRecord(
            name="event_total",
            value=len(events),
            unit="count",
            category="runtime",
        ),
        MetricRecord(
            name="runtime_started_total",
            value=event_type_counts.get("RuntimeStarted", 0),
            unit="count",
            category="runtime",
        ),
        MetricRecord(
            name="artifact_registered_total",
            value=event_type_counts.get("ArtifactRegistered", 0),
            unit="count",
            category="artifact",
        ),
        MetricRecord(
            name="artifact_routed_total",
            value=event_type_counts.get("ArtifactRouted", 0),
            unit="count",
            category="artifact",
        ),
        MetricRecord(
            name="execution_requested_total",
            value=event_type_counts.get("ExecutionRequested", 0),
            unit="count",
            category="execution",
        ),
        MetricRecord(
            name="execution_completed_total",
            value=event_type_counts.get("ExecutionCompleted", 0),
            unit="count",
            category="execution",
        ),
        MetricRecord(
            name="runtime_failed_total",
            value=event_type_counts.get("RuntimeFailed", 0),
            unit="count",
            category="runtime",
        ),
        MetricRecord(
            name="execution_success_total",
            value=execution_outcomes["execution_success_total"],
            unit="count",
            category="execution",
        ),
        MetricRecord(
            name="execution_failure_total",
            value=execution_outcomes["execution_failure_total"],
            unit="count",
            category="execution",
        ),
    ]

    for event_type, count in sorted(event_type_counts.items()):
        metrics.append(
            MetricRecord(
                name="event_type_total",
                value=count,
                unit="count",
                category="event",
                labels={
                    "event_type": event_type,
                },
            )
        )

    return metrics


def metric_records_to_map(
    metrics: list[MetricRecord],
) -> dict[str, int | float]:
    result: dict[str, int | float] = {}

    for metric in metrics:
        if metric.labels:
            continue

        result[metric.name] = metric.value

    return result


def get_consumer_summary(
    consumer_report: dict[str, Any],
) -> dict[str, Any]:
    summary = consumer_report.get("summary", {})

    if not isinstance(summary, dict):
        return {}

    return summary


def get_consumer_subscription(
    consumer_report: dict[str, Any],
) -> dict[str, Any]:
    subscription = consumer_report.get("subscription", {})

    if not isinstance(subscription, dict):
        return {}

    return subscription


def build_consumer_metrics_summary(
    consumer_report: dict[str, Any],
    base_summary: MetricsSummary | None = None,
) -> MetricsSummary:
    summary = base_summary or MetricsSummary()
    consumer_summary = get_consumer_summary(consumer_report)

    summary.accepted_events = int(consumer_summary.get("accepted_events", 0))
    summary.rejected_events = int(consumer_summary.get("rejected_events", 0))
    summary.acceptance_rate = float(consumer_summary.get("acceptance_rate", 0.0))

    return summary


def build_consumer_metric_records(
    consumer_report: dict[str, Any],
) -> list[MetricRecord]:
    summary = get_consumer_summary(consumer_report)
    subscription = get_consumer_subscription(consumer_report)

    event_types = subscription.get("event_types", [])

    if not isinstance(event_types, list):
        event_types = []

    enabled = subscription.get("enabled", False)
    status = consumer_report.get("status", "unknown")

    return [
        MetricRecord(
            name="consumer_processed_events",
            value=int(summary.get("processed_events", 0)),
            unit="count",
            category="consumer",
        ),
        MetricRecord(
            name="consumer_accepted_events",
            value=int(summary.get("accepted_events", 0)),
            unit="count",
            category="consumer",
        ),
        MetricRecord(
            name="consumer_rejected_events",
            value=int(summary.get("rejected_events", 0)),
            unit="count",
            category="consumer",
        ),
        MetricRecord(
            name="consumer_acceptance_rate",
            value=float(summary.get("acceptance_rate", 0.0)),
            unit="ratio",
            category="consumer",
        ),
        MetricRecord(
            name="consumer_result_count",
            value=int(summary.get("result_count", 0)),
            unit="count",
            category="consumer",
        ),
        MetricRecord(
            name="consumer_subscription_count",
            value=len(event_types),
            unit="count",
            category="consumer",
        ),
        MetricRecord(
            name="consumer_enabled",
            value=1 if enabled is True else 0,
            unit="boolean",
            category="consumer",
        ),
        MetricRecord(
            name="consumer_status",
            value=1 if status == "completed" else 0,
            unit="boolean",
            category="consumer",
            labels={
                "status": str(status),
            },
        ),
    ]
