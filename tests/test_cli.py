import json

from pipeline_metrics_collector.cli import main


def write_event_log(path):
    records = [
        {
            "event_type": "RuntimeStarted",
            "payload": {},
            "event_id": "event-001",
            "timestamp": "2026-07-11T06:00:00+00:00",
        },
        {
            "event_type": "ExecutionRequested",
            "payload": {
                "request_id": "request-001",
            },
            "event_id": "event-002",
            "timestamp": "2026-07-11T06:00:01+00:00",
        },
        {
            "event_type": "ExecutionCompleted",
            "payload": {
                "request_id": "request-001",
                "success": True,
            },
            "event_id": "event-003",
            "timestamp": "2026-07-11T06:00:02+00:00",
        },
    ]

    path.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )


def write_runtime_report(path):
    path.write_text(
        json.dumps(
            {
                "status": "completed",
                "summary": {
                    "artifact_count": 2,
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
                    "processed_events": 3,
                    "accepted_events": 2,
                    "rejected_events": 1,
                    "result_count": 3,
                    "acceptance_rate": 0.6666666667,
                },
            }
        ),
        encoding="utf-8",
    )


def test_cli_collect_writes_metrics_report(tmp_path):
    event_log = tmp_path / "runtime_events.jsonl"
    runtime_report = tmp_path / "runtime_report.json"
    consumer_report = tmp_path / "consumer_report.json"
    output_dir = tmp_path / "output"

    write_event_log(event_log)
    write_runtime_report(runtime_report)
    write_consumer_report(consumer_report)

    exit_code = main(
        [
            "collect",
            "--event-log",
            str(event_log),
            "--runtime-report",
            str(runtime_report),
            "--consumer-report",
            str(consumer_report),
            "--output-dir",
            str(output_dir),
            "--run-id",
            "run-cli-001",
        ]
    )

    assert exit_code == 0
    assert (output_dir / "pipeline_metrics.json").exists()


def test_cli_collect_report_contains_expected_summary(tmp_path):
    event_log = tmp_path / "runtime_events.jsonl"
    runtime_report = tmp_path / "runtime_report.json"
    consumer_report = tmp_path / "consumer_report.json"
    output_dir = tmp_path / "output"

    write_event_log(event_log)
    write_runtime_report(runtime_report)
    write_consumer_report(consumer_report)

    main(
        [
            "collect",
            "--event-log",
            str(event_log),
            "--runtime-report",
            str(runtime_report),
            "--consumer-report",
            str(consumer_report),
            "--output-dir",
            str(output_dir),
        ]
    )

    payload = json.loads(
        (output_dir / "pipeline_metrics.json").read_text(encoding="utf-8")
    )

    assert payload["status"] == "completed"
    assert payload["summary"]["event_count"] == 3
    assert payload["summary"]["artifact_count"] == 2
    assert payload["summary"]["accepted_events"] == 2
    assert payload["summary"]["rejected_events"] == 1


def test_cli_collect_without_optional_sources_is_partial(tmp_path):
    event_log = tmp_path / "runtime_events.jsonl"
    output_dir = tmp_path / "output"

    write_event_log(event_log)

    exit_code = main(
        [
            "collect",
            "--event-log",
            str(event_log),
            "--output-dir",
            str(output_dir),
        ]
    )

    payload = json.loads(
        (output_dir / "pipeline_metrics.json").read_text(encoding="utf-8")
    )

    assert exit_code == 0
    assert payload["status"] == "partial"
    assert len(payload["warnings"]) == 2


def test_cli_inspect_returns_success(tmp_path):
    event_log = tmp_path / "runtime_events.jsonl"
    output_dir = tmp_path / "output"

    write_event_log(event_log)

    main(
        [
            "collect",
            "--event-log",
            str(event_log),
            "--output-dir",
            str(output_dir),
        ]
    )

    exit_code = main(
        [
            "inspect",
            "--report",
            str(output_dir / "pipeline_metrics.json"),
        ]
    )

    assert exit_code == 0


def test_cli_validate_returns_success_for_valid_report(tmp_path):
    event_log = tmp_path / "runtime_events.jsonl"
    output_dir = tmp_path / "output"

    write_event_log(event_log)

    main(
        [
            "collect",
            "--event-log",
            str(event_log),
            "--output-dir",
            str(output_dir),
        ]
    )

    exit_code = main(
        [
            "validate",
            "--report",
            str(output_dir / "pipeline_metrics.json"),
        ]
    )

    assert exit_code == 0


def test_cli_validate_returns_failure_for_invalid_report(tmp_path):
    report_path = tmp_path / "pipeline_metrics.json"
    report_path.write_text(
        json.dumps(
            {
                "status": "completed",
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "validate",
            "--report",
            str(report_path),
        ]
    )

    assert exit_code == 1


def test_cli_validate_returns_failure_for_missing_report(tmp_path):
    exit_code = main(
        [
            "validate",
            "--report",
            str(tmp_path / "missing.json"),
        ]
    )

    assert exit_code == 1


def test_cli_collect_supports_custom_run_id(tmp_path):
    event_log = tmp_path / "runtime_events.jsonl"
    output_dir = tmp_path / "output"

    write_event_log(event_log)

    main(
        [
            "collect",
            "--event-log",
            str(event_log),
            "--output-dir",
            str(output_dir),
            "--run-id",
            "custom-run-001",
        ]
    )

    payload = json.loads(
        (output_dir / "pipeline_metrics.json").read_text(encoding="utf-8")
    )

    assert payload["run_id"] == "custom-run-001"


def test_cli_collect_report_contains_collector_version(
    tmp_path,
):
    event_log = tmp_path / "runtime_events.jsonl"
    output_dir = tmp_path / "output"

    write_event_log(event_log)

    exit_code = main(
        [
            "collect",
            "--event-log",
            str(event_log),
            "--output-dir",
            str(output_dir),
        ]
    )

    payload = json.loads(
        (output_dir / "pipeline_metrics.json").read_text(encoding="utf-8")
    )

    assert exit_code == 0
    assert payload["report_version"] == "1.0"
    assert payload["collector_version"] == "0.1.0"
