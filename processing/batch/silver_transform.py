from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_BRONZE_INPUT = "data/bronze/raw_telemetry.ndjson"
DEFAULT_SILVER_OUTPUT = "data/silver/telemetry_clean.csv"
DEFAULT_QUALITY_REPORT = "data/silver/quality_report.json"

SILVER_COLUMNS = [
    "event_id",
    "event_ts",
    "event_date",
    "event_minute",
    "ingested_at",
    "written_at",
    "ingestion_latency_ms",
    "equipment_id",
    "site",
    "line",
    "operational_state",
    "temperature_c",
    "vibration_mm_s",
    "lubrication_pressure_bar",
    "rpm",
    "amperage_a",
    "power_kw",
    "flow_m3_h",
    "anomaly_score",
    "quality_flag",
    "is_anomaly",
    "is_quality_issue",
    "is_flow_missing",
    "risk_level",
]


@dataclass
class SilverResult:
    input_records: int = 0
    output_records: int = 0
    duplicate_events_skipped: int = 0
    malformed_records_skipped: int = 0
    anomaly_events: int = 0
    quality_issue_events: int = 0
    flow_missing_events: int = 0


def load_bronze_records(input_path: str) -> Iterable[dict[str, Any]]:
    path = Path(input_path)
    if not path.exists():
        return

    with path.open("r", encoding="utf-8") as file_handle:
        for line in file_handle:
            if line.strip():
                yield json.loads(line)


def transform_bronze_record(record: dict[str, Any]) -> dict[str, Any]:
    payload = record["payload"]
    event_ts = parse_timestamp(payload["event_ts"])
    written_at = parse_timestamp(record["written_at"])
    ingested_at_value = record.get("ingested_at") or record["written_at"]
    ingested_at = parse_timestamp(ingested_at_value)

    anomaly_score = float(payload["anomaly_score"])
    quality_flag = payload["quality_flag"]
    flow = payload.get("flow_m3_h")
    is_anomaly = anomaly_score >= 0.7 or quality_flag == "anomalous"
    is_quality_issue = quality_flag != "ok"
    is_flow_missing = flow is None

    return {
        "event_id": payload["event_id"],
        "event_ts": event_ts.isoformat(),
        "event_date": event_ts.date().isoformat(),
        "event_minute": event_ts.replace(second=0, microsecond=0).isoformat(),
        "ingested_at": ingested_at.isoformat(),
        "written_at": written_at.isoformat(),
        "ingestion_latency_ms": round((ingested_at - event_ts).total_seconds() * 1000, 2),
        "equipment_id": payload["equipment_id"],
        "site": payload["site"],
        "line": payload["line"],
        "operational_state": payload["operational_state"],
        "temperature_c": float(payload["temperature_c"]),
        "vibration_mm_s": float(payload["vibration_mm_s"]),
        "lubrication_pressure_bar": float(payload["lubrication_pressure_bar"]),
        "rpm": float(payload["rpm"]),
        "amperage_a": float(payload["amperage_a"]),
        "power_kw": float(payload["power_kw"]),
        "flow_m3_h": "" if flow is None else float(flow),
        "anomaly_score": anomaly_score,
        "quality_flag": quality_flag,
        "is_anomaly": is_anomaly,
        "is_quality_issue": is_quality_issue,
        "is_flow_missing": is_flow_missing,
        "risk_level": classify_risk(payload, anomaly_score, is_quality_issue),
    }


def build_silver_dataset(input_path: str, output_path: str, quality_report_path: str) -> SilverResult:
    result = SilverResult()
    seen_event_ids: set[str] = set()
    rows: list[dict[str, Any]] = []

    for record in load_bronze_records(input_path):
        result.input_records += 1
        try:
            row = transform_bronze_record(record)
        except (KeyError, TypeError, ValueError) as exc:
            result.malformed_records_skipped += 1
            continue

        if row["event_id"] in seen_event_ids:
            result.duplicate_events_skipped += 1
            continue

        seen_event_ids.add(row["event_id"])
        rows.append(row)
        result.output_records += 1
        result.anomaly_events += int(row["is_anomaly"])
        result.quality_issue_events += int(row["is_quality_issue"])
        result.flow_missing_events += int(row["is_flow_missing"])

    write_silver_csv(output_path, rows)
    write_quality_report(quality_report_path, result)
    return result


def write_silver_csv(output_path: str, rows: list[dict[str, Any]]) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=SILVER_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def write_quality_report(output_path: str, result: SilverResult) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "input_records": result.input_records,
        "output_records": result.output_records,
        "duplicate_events_skipped": result.duplicate_events_skipped,
        "malformed_records_skipped": result.malformed_records_skipped,
        "anomaly_events": result.anomaly_events,
        "quality_issue_events": result.quality_issue_events,
        "flow_missing_events": result.flow_missing_events,
    }
    with path.open("w", encoding="utf-8") as file_handle:
        json.dump(report, file_handle, indent=2)
        file_handle.write("\n")


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def classify_risk(payload: dict[str, Any], anomaly_score: float, is_quality_issue: bool) -> str:
    if payload["operational_state"] == "critical":
        return "critical"
    if float(payload["temperature_c"]) >= 82 or float(payload["lubrication_pressure_bar"]) < 2.2:
        return "critical"
    if payload["operational_state"] == "warning":
        return "warning"
    if anomaly_score >= 0.7 or is_quality_issue:
        return "warning"
    return "normal"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the local silver telemetry dataset.")
    parser.add_argument("--input", default=DEFAULT_BRONZE_INPUT)
    parser.add_argument("--output", default=DEFAULT_SILVER_OUTPUT)
    parser.add_argument("--quality-report", default=DEFAULT_QUALITY_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_silver_dataset(args.input, args.output, args.quality_report)
    print(
        "silver dataset built "
        f"input_records={result.input_records} "
        f"output_records={result.output_records} "
        f"malformed_records_skipped={result.malformed_records_skipped}"
    )


if __name__ == "__main__":
    main()
