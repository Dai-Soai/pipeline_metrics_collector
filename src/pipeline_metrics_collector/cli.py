from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pipeline_metrics_collector.collector import (
    collect_pipeline_metrics,
)
from pipeline_metrics_collector.contract import (
    metrics_report_to_dict,
)
from pipeline_metrics_collector.report import (
    build_metrics_report,
    build_metrics_report_inspection,
    read_metrics_report,
    validate_metrics_report_data,
    write_metrics_report,
)


def print_json(
    payload: dict[str, Any] | list[Any],
) -> None:
    print(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        )
    )


def cmd_collect(
    args: argparse.Namespace,
) -> int:
    collection = collect_pipeline_metrics(
        event_log_path=args.event_log,
        runtime_report_path=args.runtime_report,
        consumer_report_path=args.consumer_report,
    )

    report = build_metrics_report(
        collection=collection,
        run_id=args.run_id,
    )

    if args.output_dir is None:
        print_json(
            metrics_report_to_dict(report)
        )
        return 0

    report_path = write_metrics_report(
        report=report,
        output_dir=args.output_dir,
    )

    print_json(
        {
            "status": "written",
            "report_path": str(report_path),
            "report": metrics_report_to_dict(report),
        }
    )

    return 0


def cmd_inspect(
    args: argparse.Namespace,
) -> int:
    report = read_metrics_report(
        args.report
    )

    print_json(
        build_metrics_report_inspection(report)
    )

    return 0


def cmd_validate(
    args: argparse.Namespace,
) -> int:
    report_path = Path(args.report)

    if not report_path.exists():
        print_json(
            {
                "valid": False,
                "report_path": str(report_path),
                "errors": [
                    f"Metrics report not found: {report_path}"
                ],
            }
        )
        return 1

    try:
        payload = json.loads(
            report_path.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as exc:
        print_json(
            {
                "valid": False,
                "report_path": str(report_path),
                "errors": [
                    f"Invalid JSON: {exc.msg}"
                ],
            }
        )
        return 1

    if not isinstance(payload, dict):
        print_json(
            {
                "valid": False,
                "report_path": str(report_path),
                "errors": [
                    "Metrics report must contain a JSON object"
                ],
            }
        )
        return 1

    errors = validate_metrics_report_data(
        payload
    )

    print_json(
        {
            "valid": not errors,
            "report_path": str(report_path),
            "errors": errors,
        }
    )

    return 0 if not errors else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pipeline-metrics",
        description="Pipeline Metrics Collector CLI",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    collect_parser = subparsers.add_parser(
        "collect",
        help="Collect pipeline runtime metrics",
    )
    collect_parser.add_argument(
        "--event-log",
        required=True,
        help="Runtime JSONL event log",
    )
    collect_parser.add_argument(
        "--runtime-report",
        default=None,
        help="Optional runtime JSON report",
    )
    collect_parser.add_argument(
        "--consumer-report",
        default=None,
        help="Optional consumer JSON report",
    )
    collect_parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for pipeline_metrics.json",
    )
    collect_parser.add_argument(
        "--run-id",
        default=None,
        help="Optional metrics collection run identifier",
    )
    collect_parser.set_defaults(
        func=cmd_collect
    )

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect a generated metrics report",
    )
    inspect_parser.add_argument(
        "--report",
        required=True,
        help="Path to pipeline_metrics.json",
    )
    inspect_parser.set_defaults(
        func=cmd_inspect
    )

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a generated metrics report",
    )
    validate_parser.add_argument(
        "--report",
        required=True,
        help="Path to pipeline_metrics.json",
    )
    validate_parser.set_defaults(
        func=cmd_validate
    )

    return parser


def main(
    argv: list[str] | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
