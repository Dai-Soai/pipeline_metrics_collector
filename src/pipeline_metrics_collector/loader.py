from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline_metrics_collector.contract import MetricsSource


def build_metrics_source(
    source_type: str,
    path: str | Path,
    metadata: dict[str, Any] | None = None,
) -> MetricsSource:
    source_path = Path(path)
    exists = source_path.exists()

    return MetricsSource(
        source_type=source_type,
        path=str(source_path),
        exists=exists,
        size_bytes=source_path.stat().st_size if exists else 0,
        metadata=dict(metadata or {}),
    )


def read_json_file(
    path: str | Path,
) -> dict[str, Any]:
    source_path = Path(path)

    if not source_path.exists():
        raise FileNotFoundError(f"JSON source not found: {source_path}")

    text = source_path.read_text(encoding="utf-8")

    if not text.strip():
        raise ValueError(f"JSON source is empty: {source_path}")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON source {source_path}: {exc.msg}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"JSON source must contain an object: {source_path}"
        )

    return data


def parse_jsonl_line(
    line: str,
    line_number: int,
    path: str | Path,
) -> dict[str, Any]:
    try:
        data = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSONL source {path} at line {line_number}: {exc.msg}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"JSONL source {path} at line {line_number} "
            "must contain an object"
        )

    return data


def read_jsonl_file(
    path: str | Path,
) -> list[dict[str, Any]]:
    source_path = Path(path)

    if not source_path.exists():
        raise FileNotFoundError(f"JSONL source not found: {source_path}")

    lines = source_path.read_text(
        encoding="utf-8",
    ).splitlines()

    records: list[dict[str, Any]] = []

    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue

        records.append(
            parse_jsonl_line(
                line=line,
                line_number=line_number,
                path=source_path,
            )
        )

    return records


def load_runtime_events(
    path: str | Path,
) -> tuple[MetricsSource, list[dict[str, Any]]]:
    records = read_jsonl_file(path)

    source = build_metrics_source(
        source_type="runtime_event_log",
        path=path,
        metadata={
            "format": "jsonl",
            "record_count": len(records),
        },
    )

    return source, records


def load_runtime_report(
    path: str | Path,
) -> tuple[MetricsSource, dict[str, Any]]:
    report = read_json_file(path)

    source = build_metrics_source(
        source_type="runtime_report",
        path=path,
        metadata={
            "format": "json",
            "status": report.get("status"),
        },
    )

    return source, report


def load_consumer_report(
    path: str | Path,
) -> tuple[MetricsSource, dict[str, Any]]:
    report = read_json_file(path)

    source = build_metrics_source(
        source_type="consumer_report",
        path=path,
        metadata={
            "format": "json",
            "status": report.get("status"),
            "report_version": report.get("report_version"),
        },
    )

    return source, report
