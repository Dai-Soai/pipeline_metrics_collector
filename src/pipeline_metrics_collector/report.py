from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from pipeline_metrics_collector.collector import (
    MetricsCollection,
    collection_status,
)
from pipeline_metrics_collector.contract import (
    MetricsReport,
    metrics_report_from_dict,
    metrics_report_to_dict,
)


METRICS_REPORT_FILENAME = "pipeline_metrics.json"
METRICS_REPORT_VERSION = "1.0"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_metrics_report(
    collection: MetricsCollection,
    run_id: str | None = None,
) -> MetricsReport:
    return MetricsReport(
        report_version=METRICS_REPORT_VERSION,
        run_id=run_id or str(uuid4()),
        generated_at=utc_now_iso(),
        status=collection_status(collection),
        sources=list(collection.sources),
        summary=collection.summary,
        metrics=list(collection.metrics),
        warnings=list(collection.warnings),
    )


def get_metrics_report_path(
    output_dir: str | Path,
) -> Path:
    return Path(output_dir) / METRICS_REPORT_FILENAME


def write_metrics_report(
    report: MetricsReport,
    output_dir: str | Path,
) -> Path:
    report_path = get_metrics_report_path(output_dir)
    report_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = metrics_report_to_dict(report)

    report_path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return report_path


def read_metrics_report(
    path: str | Path,
) -> MetricsReport:
    report_path = Path(path)

    if not report_path.exists():
        raise FileNotFoundError(
            f"Metrics report not found: {report_path}"
        )

    text = report_path.read_text(
        encoding="utf-8",
    )

    if not text.strip():
        raise ValueError(
            f"Metrics report is empty: {report_path}"
        )

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid metrics report JSON: {exc.msg}"
        ) from exc

    if not isinstance(payload, dict):
        raise ValueError(
            "Metrics report must contain a JSON object"
        )

    validation_errors = validate_metrics_report_data(
        payload
    )

    if validation_errors:
        raise ValueError(
            "Invalid metrics report: "
            + "; ".join(validation_errors)
        )

    return metrics_report_from_dict(payload)


def validate_metrics_report_data(
    payload: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    required_fields = {
        "report_version",
        "run_id",
        "generated_at",
        "status",
        "sources",
        "summary",
        "metrics",
        "warnings",
    }

    for field_name in sorted(required_fields):
        if field_name not in payload:
            errors.append(
                f"Missing required field: {field_name}"
            )

    if "report_version" in payload and not isinstance(
        payload["report_version"],
        str,
    ):
        errors.append(
            "report_version must be a string"
        )

    if "run_id" in payload and not isinstance(
        payload["run_id"],
        str,
    ):
        errors.append(
            "run_id must be a string"
        )

    if "status" in payload and payload["status"] not in {
        "completed",
        "partial",
        "empty",
    }:
        errors.append(
            "status must be completed, partial or empty"
        )

    if "sources" in payload and not isinstance(
        payload["sources"],
        list,
    ):
        errors.append(
            "sources must be a list"
        )

    if "summary" in payload and not isinstance(
        payload["summary"],
        dict,
    ):
        errors.append(
            "summary must be an object"
        )

    metrics = payload.get("metrics")

    if metrics is not None and not isinstance(
        metrics,
        list,
    ):
        errors.append(
            "metrics must be a list"
        )
    elif isinstance(metrics, list):
        for index, metric in enumerate(metrics):
            if not isinstance(metric, dict):
                errors.append(
                    f"metrics[{index}] must be an object"
                )
                continue

            if "name" not in metric:
                errors.append(
                    f"metrics[{index}] is missing name"
                )

            if "value" not in metric:
                errors.append(
                    f"metrics[{index}] is missing value"
                )

    if "warnings" in payload and not isinstance(
        payload["warnings"],
        list,
    ):
        errors.append(
            "warnings must be a list"
        )

    return errors


def build_metrics_report_inspection(
    report: MetricsReport,
) -> dict[str, Any]:
    return {
        "report_version": report.report_version,
        "run_id": report.run_id,
        "generated_at": report.generated_at,
        "status": report.status,
        "source_count": len(report.sources),
        "metric_count": len(report.metrics),
        "warning_count": len(report.warnings),
        "summary": {
            "event_count": report.summary.event_count,
            "artifact_count": report.summary.artifact_count,
            "execution_requested": (
                report.summary.execution_requested
            ),
            "execution_completed": (
                report.summary.execution_completed
            ),
            "runtime_failed": (
                report.summary.runtime_failed
            ),
            "accepted_events": (
                report.summary.accepted_events
            ),
            "rejected_events": (
                report.summary.rejected_events
            ),
            "acceptance_rate": (
                report.summary.acceptance_rate
            ),
        },
    }
