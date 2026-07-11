from __future__ import annotations

from datetime import datetime
from typing import Any

from pipeline_metrics_collector.contract import MetricRecord


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def get_request_id(event: dict[str, Any]) -> str | None:
    payload = event.get("payload", {})

    if not isinstance(payload, dict):
        return None

    request_id = payload.get("request_id")

    if not isinstance(request_id, str) or not request_id.strip():
        return None

    return request_id


def milliseconds_between(
    start: datetime,
    end: datetime,
) -> float:
    return (end - start).total_seconds() * 1000.0


def collect_execution_latencies(
    events: list[dict[str, Any]],
) -> tuple[list[float], list[str]]:
    requests: dict[str, datetime] = {}
    completions: dict[str, datetime] = {}
    warnings: list[str] = []

    for index, event in enumerate(events, start=1):
        event_type = event.get("event_type")
        request_id = get_request_id(event)

        if event_type not in {
            "ExecutionRequested",
            "ExecutionCompleted",
        }:
            continue

        if request_id is None:
            warnings.append(
                f"{event_type} event at index {index} "
                "does not contain a valid request_id"
            )
            continue

        timestamp = parse_timestamp(event.get("timestamp"))

        if timestamp is None:
            warnings.append(
                f"{event_type} event for request_id "
                f"{request_id} has an invalid timestamp"
            )
            continue

        if event_type == "ExecutionRequested":
            requests[request_id] = timestamp
        else:
            completions[request_id] = timestamp

    latencies: list[float] = []

    for request_id, requested_at in requests.items():
        completed_at = completions.get(request_id)

        if completed_at is None:
            warnings.append(
                f"No ExecutionCompleted event for request_id {request_id}"
            )
            continue

        latency_ms = milliseconds_between(
            start=requested_at,
            end=completed_at,
        )

        if latency_ms < 0:
            warnings.append(
                f"ExecutionCompleted precedes ExecutionRequested "
                f"for request_id {request_id}"
            )
            continue

        latencies.append(latency_ms)

    for request_id in completions:
        if request_id not in requests:
            warnings.append(
                f"No ExecutionRequested event for request_id {request_id}"
            )

    return latencies, warnings


def calculate_latency_statistics(
    latencies: list[float],
) -> dict[str, float | int]:
    if not latencies:
        return {
            "matched_execution_count": 0,
            "average_execution_latency_ms": 0.0,
            "minimum_execution_latency_ms": 0.0,
            "maximum_execution_latency_ms": 0.0,
        }

    return {
        "matched_execution_count": len(latencies),
        "average_execution_latency_ms": sum(latencies) / len(latencies),
        "minimum_execution_latency_ms": min(latencies),
        "maximum_execution_latency_ms": max(latencies),
    }


def calculate_runtime_duration_ms(
    events: list[dict[str, Any]],
) -> tuple[float, list[str]]:
    timestamps: list[datetime] = []
    warnings: list[str] = []

    for index, event in enumerate(events, start=1):
        timestamp = parse_timestamp(event.get("timestamp"))

        if timestamp is None:
            warnings.append(
                f"Event at index {index} has an invalid timestamp"
            )
            continue

        timestamps.append(timestamp)

    if len(timestamps) < 2:
        return 0.0, warnings

    duration_ms = milliseconds_between(
        start=min(timestamps),
        end=max(timestamps),
    )

    return duration_ms, warnings


def build_latency_metric_records(
    events: list[dict[str, Any]],
) -> tuple[list[MetricRecord], list[str]]:
    latencies, execution_warnings = collect_execution_latencies(events)
    statistics = calculate_latency_statistics(latencies)

    runtime_duration_ms, duration_warnings = (
        calculate_runtime_duration_ms(events)
    )

    metrics = [
        MetricRecord(
            name="matched_execution_count",
            value=statistics["matched_execution_count"],
            unit="count",
            category="latency",
        ),
        MetricRecord(
            name="average_execution_latency_ms",
            value=statistics["average_execution_latency_ms"],
            unit="milliseconds",
            category="latency",
        ),
        MetricRecord(
            name="minimum_execution_latency_ms",
            value=statistics["minimum_execution_latency_ms"],
            unit="milliseconds",
            category="latency",
        ),
        MetricRecord(
            name="maximum_execution_latency_ms",
            value=statistics["maximum_execution_latency_ms"],
            unit="milliseconds",
            category="latency",
        ),
        MetricRecord(
            name="runtime_duration_ms",
            value=runtime_duration_ms,
            unit="milliseconds",
            category="runtime",
        ),
    ]

    for index, latency_ms in enumerate(latencies, start=1):
        metrics.append(
            MetricRecord(
                name="execution_latency_ms",
                value=latency_ms,
                unit="milliseconds",
                category="latency",
                labels={
                    "sample": str(index),
                },
            )
        )

    warnings = execution_warnings + duration_warnings

    return metrics, warnings
