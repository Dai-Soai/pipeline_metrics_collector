from datetime import datetime, timezone

from pipeline_metrics_collector.latency import (
    build_latency_metric_records,
    calculate_latency_statistics,
    calculate_runtime_duration_ms,
    collect_execution_latencies,
    get_request_id,
    milliseconds_between,
    parse_timestamp,
)


def make_event(
    event_type: str,
    timestamp: str,
    request_id: str | None = None,
) -> dict:
    payload = {}

    if request_id is not None:
        payload["request_id"] = request_id

    return {
        "event_type": event_type,
        "payload": payload,
        "event_id": f"{event_type}-{request_id}",
        "timestamp": timestamp,
    }


def test_parse_timestamp_returns_datetime():
    timestamp = parse_timestamp(
        "2026-07-11T06:00:00+00:00"
    )

    assert timestamp is not None
    assert timestamp.tzinfo is not None


def test_parse_timestamp_returns_none_for_invalid_value():
    assert parse_timestamp("invalid") is None
    assert parse_timestamp(None) is None


def test_get_request_id_returns_request_id():
    event = make_event(
        "ExecutionRequested",
        "2026-07-11T06:00:00+00:00",
        "request-001",
    )

    assert get_request_id(event) == "request-001"


def test_get_request_id_returns_none_when_missing():
    event = make_event(
        "RuntimeStarted",
        "2026-07-11T06:00:00+00:00",
    )

    assert get_request_id(event) is None


def test_milliseconds_between():
    start = datetime(
        2026,
        7,
        11,
        6,
        0,
        0,
        tzinfo=timezone.utc,
    )
    end = datetime(
        2026,
        7,
        11,
        6,
        0,
        1,
        500000,
        tzinfo=timezone.utc,
    )

    assert milliseconds_between(start, end) == 1500.0


def test_collect_execution_latencies_matches_request_and_completion():
    events = [
        make_event(
            "ExecutionRequested",
            "2026-07-11T06:00:00+00:00",
            "request-001",
        ),
        make_event(
            "ExecutionCompleted",
            "2026-07-11T06:00:01.250000+00:00",
            "request-001",
        ),
    ]

    latencies, warnings = collect_execution_latencies(events)

    assert latencies == [1250.0]
    assert warnings == []


def test_collect_execution_latencies_supports_multiple_requests():
    events = [
        make_event(
            "ExecutionRequested",
            "2026-07-11T06:00:00+00:00",
            "request-001",
        ),
        make_event(
            "ExecutionRequested",
            "2026-07-11T06:00:02+00:00",
            "request-002",
        ),
        make_event(
            "ExecutionCompleted",
            "2026-07-11T06:00:01+00:00",
            "request-001",
        ),
        make_event(
            "ExecutionCompleted",
            "2026-07-11T06:00:04+00:00",
            "request-002",
        ),
    ]

    latencies, warnings = collect_execution_latencies(events)

    assert latencies == [1000.0, 2000.0]
    assert warnings == []


def test_collect_execution_latencies_warns_for_unmatched_request():
    events = [
        make_event(
            "ExecutionRequested",
            "2026-07-11T06:00:00+00:00",
            "request-001",
        ),
    ]

    latencies, warnings = collect_execution_latencies(events)

    assert latencies == []
    assert any(
        "No ExecutionCompleted" in warning
        for warning in warnings
    )


def test_collect_execution_latencies_warns_for_unmatched_completion():
    events = [
        make_event(
            "ExecutionCompleted",
            "2026-07-11T06:00:01+00:00",
            "request-001",
        ),
    ]

    latencies, warnings = collect_execution_latencies(events)

    assert latencies == []
    assert any(
        "No ExecutionRequested" in warning
        for warning in warnings
    )


def test_collect_execution_latencies_warns_for_invalid_timestamp():
    events = [
        make_event(
            "ExecutionRequested",
            "invalid",
            "request-001",
        ),
    ]

    latencies, warnings = collect_execution_latencies(events)

    assert latencies == []
    assert any(
        "invalid timestamp" in warning
        for warning in warnings
    )


def test_collect_execution_latencies_rejects_negative_latency():
    events = [
        make_event(
            "ExecutionRequested",
            "2026-07-11T06:00:02+00:00",
            "request-001",
        ),
        make_event(
            "ExecutionCompleted",
            "2026-07-11T06:00:01+00:00",
            "request-001",
        ),
    ]

    latencies, warnings = collect_execution_latencies(events)

    assert latencies == []
    assert any(
        "precedes" in warning
        for warning in warnings
    )


def test_calculate_latency_statistics():
    statistics = calculate_latency_statistics(
        [1000.0, 2000.0, 3000.0]
    )

    assert statistics["matched_execution_count"] == 3
    assert statistics["average_execution_latency_ms"] == 2000.0
    assert statistics["minimum_execution_latency_ms"] == 1000.0
    assert statistics["maximum_execution_latency_ms"] == 3000.0


def test_calculate_latency_statistics_handles_empty_values():
    statistics = calculate_latency_statistics([])

    assert statistics["matched_execution_count"] == 0
    assert statistics["average_execution_latency_ms"] == 0.0
    assert statistics["minimum_execution_latency_ms"] == 0.0
    assert statistics["maximum_execution_latency_ms"] == 0.0


def test_calculate_runtime_duration_ms():
    events = [
        make_event(
            "RuntimeStarted",
            "2026-07-11T06:00:00+00:00",
        ),
        make_event(
            "ExecutionCompleted",
            "2026-07-11T06:00:03.500000+00:00",
            "request-001",
        ),
    ]

    duration_ms, warnings = calculate_runtime_duration_ms(events)

    assert duration_ms == 3500.0
    assert warnings == []


def test_calculate_runtime_duration_ms_handles_single_event():
    events = [
        make_event(
            "RuntimeStarted",
            "2026-07-11T06:00:00+00:00",
        ),
    ]

    duration_ms, warnings = calculate_runtime_duration_ms(events)

    assert duration_ms == 0.0
    assert warnings == []


def test_build_latency_metric_records():
    events = [
        make_event(
            "RuntimeStarted",
            "2026-07-11T06:00:00+00:00",
        ),
        make_event(
            "ExecutionRequested",
            "2026-07-11T06:00:01+00:00",
            "request-001",
        ),
        make_event(
            "ExecutionCompleted",
            "2026-07-11T06:00:02.500000+00:00",
            "request-001",
        ),
    ]

    metrics, warnings = build_latency_metric_records(events)

    metric_map = {
        metric.name: metric.value
        for metric in metrics
        if not metric.labels
    }

    assert metric_map["matched_execution_count"] == 1
    assert metric_map["average_execution_latency_ms"] == 1500.0
    assert metric_map["minimum_execution_latency_ms"] == 1500.0
    assert metric_map["maximum_execution_latency_ms"] == 1500.0
    assert metric_map["runtime_duration_ms"] == 2500.0
    assert warnings == []


def test_build_latency_metric_records_contains_latency_samples():
    events = [
        make_event(
            "ExecutionRequested",
            "2026-07-11T06:00:00+00:00",
            "request-001",
        ),
        make_event(
            "ExecutionCompleted",
            "2026-07-11T06:00:01+00:00",
            "request-001",
        ),
    ]

    metrics, _ = build_latency_metric_records(events)

    sample = next(
        metric
        for metric in metrics
        if metric.name == "execution_latency_ms"
    )

    assert sample.value == 1000.0
    assert sample.labels == {
        "sample": "1",
    }
