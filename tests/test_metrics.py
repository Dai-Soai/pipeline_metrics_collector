from pipeline_metrics_collector.metrics import (
    build_runtime_metric_records,
    build_runtime_metrics_summary,
    count_event_types,
    count_execution_outcomes,
    get_event_type,
    metric_records_to_map,
)


def make_event(
    event_type: str,
    payload: dict | None = None,
) -> dict:
    return {
        "event_type": event_type,
        "payload": payload or {},
        "event_id": f"{event_type}-001",
        "timestamp": "2026-07-11T06:00:00+00:00",
    }


def test_get_event_type_returns_event_type():
    event = make_event("RuntimeStarted")

    assert get_event_type(event) == "RuntimeStarted"


def test_get_event_type_returns_unknown_for_missing_value():
    assert get_event_type({}) == "Unknown"


def test_get_event_type_returns_unknown_for_invalid_value():
    assert get_event_type({"event_type": 123}) == "Unknown"
    assert get_event_type({"event_type": ""}) == "Unknown"


def test_count_event_types_counts_events():
    events = [
        make_event("RuntimeStarted"),
        make_event("ArtifactRegistered"),
        make_event("ExecutionCompleted"),
        make_event("ExecutionCompleted"),
    ]

    counts = count_event_types(events)

    assert counts == {
        "RuntimeStarted": 1,
        "ArtifactRegistered": 1,
        "ExecutionCompleted": 2,
    }


def test_count_event_types_counts_unknown_events():
    events = [
        {},
        {"event_type": None},
        make_event("RuntimeStarted"),
    ]

    counts = count_event_types(events)

    assert counts["Unknown"] == 2
    assert counts["RuntimeStarted"] == 1


def test_count_execution_outcomes_counts_success_and_failure():
    events = [
        make_event(
            "ExecutionCompleted",
            {"success": True},
        ),
        make_event(
            "ExecutionCompleted",
            {"success": False},
        ),
        make_event(
            "ExecutionCompleted",
            {},
        ),
        make_event("RuntimeStarted"),
    ]

    outcomes = count_execution_outcomes(events)

    assert outcomes == {
        "execution_success_total": 1,
        "execution_failure_total": 2,
    }


def test_build_runtime_metrics_summary():
    events = [
        make_event("RuntimeStarted"),
        make_event("ArtifactRegistered"),
        make_event("ExecutionRequested"),
        make_event(
            "ExecutionCompleted",
            {"success": True},
        ),
        make_event("RuntimeFailed"),
    ]

    summary = build_runtime_metrics_summary(
        events=events,
        artifact_count=2,
    )

    assert summary.event_count == 5
    assert summary.artifact_count == 2
    assert summary.execution_requested == 1
    assert summary.execution_completed == 1
    assert summary.runtime_failed == 1


def test_build_runtime_metric_records_contains_core_metrics():
    events = [
        make_event("RuntimeStarted"),
        make_event("ArtifactRegistered"),
        make_event("ArtifactRouted"),
        make_event("ExecutionRequested"),
        make_event(
            "ExecutionCompleted",
            {"success": True},
        ),
    ]

    metrics = build_runtime_metric_records(events)
    metric_map = metric_records_to_map(metrics)

    assert metric_map["event_total"] == 5
    assert metric_map["runtime_started_total"] == 1
    assert metric_map["artifact_registered_total"] == 1
    assert metric_map["artifact_routed_total"] == 1
    assert metric_map["execution_requested_total"] == 1
    assert metric_map["execution_completed_total"] == 1
    assert metric_map["runtime_failed_total"] == 0
    assert metric_map["execution_success_total"] == 1
    assert metric_map["execution_failure_total"] == 0


def test_build_runtime_metric_records_contains_event_type_labels():
    events = [
        make_event("RuntimeStarted"),
        make_event("ExecutionCompleted"),
        make_event("ExecutionCompleted"),
    ]

    metrics = build_runtime_metric_records(events)

    event_type_metrics = [
        metric
        for metric in metrics
        if metric.name == "event_type_total"
    ]

    values = {
        metric.labels["event_type"]: metric.value
        for metric in event_type_metrics
    }

    assert values == {
        "ExecutionCompleted": 2,
        "RuntimeStarted": 1,
    }


def test_metric_records_to_map_skips_labelled_metrics():
    events = [
        make_event("RuntimeStarted"),
    ]

    metrics = build_runtime_metric_records(events)
    metric_map = metric_records_to_map(metrics)

    assert "event_total" in metric_map
    assert "event_type_total" not in metric_map
