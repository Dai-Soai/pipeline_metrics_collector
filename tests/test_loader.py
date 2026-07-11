import json

import pytest

from pipeline_metrics_collector.loader import (
    build_metrics_source,
    load_consumer_report,
    load_runtime_events,
    load_runtime_report,
    parse_jsonl_line,
    read_json_file,
    read_jsonl_file,
)


def test_build_metrics_source_for_existing_file(tmp_path):
    source_path = tmp_path / "runtime_report.json"
    source_path.write_text("{}", encoding="utf-8")

    source = build_metrics_source(
        source_type="runtime_report",
        path=source_path,
        metadata={"format": "json"},
    )

    assert source.source_type == "runtime_report"
    assert source.path == str(source_path)
    assert source.exists is True
    assert source.size_bytes == 2
    assert source.metadata["format"] == "json"


def test_build_metrics_source_for_missing_file(tmp_path):
    source_path = tmp_path / "missing.json"

    source = build_metrics_source(
        source_type="consumer_report",
        path=source_path,
    )

    assert source.exists is False
    assert source.size_bytes == 0
    assert source.metadata == {}


def test_read_json_file_returns_object(tmp_path):
    source_path = tmp_path / "report.json"
    source_path.write_text(
        json.dumps({"status": "completed"}),
        encoding="utf-8",
    )

    data = read_json_file(source_path)

    assert data["status"] == "completed"


def test_read_json_file_raises_for_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_json_file(tmp_path / "missing.json")


def test_read_json_file_raises_for_empty_file(tmp_path):
    source_path = tmp_path / "empty.json"
    source_path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="empty"):
        read_json_file(source_path)


def test_read_json_file_raises_for_invalid_json(tmp_path):
    source_path = tmp_path / "invalid.json"
    source_path.write_text("{invalid-json}", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid JSON source"):
        read_json_file(source_path)


def test_read_json_file_requires_json_object(tmp_path):
    source_path = tmp_path / "list.json"
    source_path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="must contain an object"):
        read_json_file(source_path)


def test_parse_jsonl_line_returns_object():
    record = parse_jsonl_line(
        line='{"event_type":"RuntimeStarted"}',
        line_number=1,
        path="runtime_events.jsonl",
    )

    assert record["event_type"] == "RuntimeStarted"


def test_parse_jsonl_line_raises_for_invalid_json():
    with pytest.raises(ValueError, match="line 3"):
        parse_jsonl_line(
            line="{invalid-json}",
            line_number=3,
            path="runtime_events.jsonl",
        )


def test_parse_jsonl_line_requires_json_object():
    with pytest.raises(ValueError, match="must contain an object"):
        parse_jsonl_line(
            line="[]",
            line_number=2,
            path="runtime_events.jsonl",
        )


def test_read_jsonl_file_reads_records_and_skips_blank_lines(tmp_path):
    source_path = tmp_path / "runtime_events.jsonl"
    source_path.write_text(
        '{"event_type":"RuntimeStarted"}\n\n'
        '{"event_type":"ExecutionCompleted"}\n',
        encoding="utf-8",
    )

    records = read_jsonl_file(source_path)

    assert len(records) == 2
    assert records[0]["event_type"] == "RuntimeStarted"
    assert records[1]["event_type"] == "ExecutionCompleted"


def test_read_jsonl_file_preserves_order(tmp_path):
    source_path = tmp_path / "runtime_events.jsonl"
    source_path.write_text(
        '{"event_type":"RuntimeStarted"}\n'
        '{"event_type":"ArtifactRegistered"}\n'
        '{"event_type":"ExecutionCompleted"}\n',
        encoding="utf-8",
    )

    records = read_jsonl_file(source_path)

    assert [
        record["event_type"]
        for record in records
    ] == [
        "RuntimeStarted",
        "ArtifactRegistered",
        "ExecutionCompleted",
    ]


def test_read_jsonl_file_raises_for_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_jsonl_file(tmp_path / "missing.jsonl")


def test_load_runtime_events_returns_source_and_records(tmp_path):
    source_path = tmp_path / "runtime_events.jsonl"
    source_path.write_text(
        '{"event_type":"RuntimeStarted"}\n'
        '{"event_type":"ExecutionCompleted"}\n',
        encoding="utf-8",
    )

    source, records = load_runtime_events(source_path)

    assert source.source_type == "runtime_event_log"
    assert source.exists is True
    assert source.metadata["format"] == "jsonl"
    assert source.metadata["record_count"] == 2
    assert len(records) == 2


def test_load_runtime_report_returns_source_and_report(tmp_path):
    source_path = tmp_path / "runtime_report.json"
    source_path.write_text(
        json.dumps({
            "status": "completed",
            "summary": {
                "artifact_count": 2,
            },
        }),
        encoding="utf-8",
    )

    source, report = load_runtime_report(source_path)

    assert source.source_type == "runtime_report"
    assert source.metadata["status"] == "completed"
    assert report["summary"]["artifact_count"] == 2


def test_load_consumer_report_returns_source_and_report(tmp_path):
    source_path = tmp_path / "consumer_report.json"
    source_path.write_text(
        json.dumps({
            "report_version": "1.0",
            "status": "completed",
            "summary": {
                "accepted_events": 3,
                "rejected_events": 2,
            },
        }),
        encoding="utf-8",
    )

    source, report = load_consumer_report(source_path)

    assert source.source_type == "consumer_report"
    assert source.metadata["report_version"] == "1.0"
    assert source.metadata["status"] == "completed"
    assert report["summary"]["accepted_events"] == 3
