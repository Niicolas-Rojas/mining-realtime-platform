from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


DEFAULT_SILVER_INPUT = "data/silver/telemetry_clean.csv"
DEFAULT_GOLD_OUTPUT = "data/gold/equipment_minute_summary.csv"
DEFAULT_GOLD_REPORT = "data/gold/gold_quality_report.json"

GROUP_KEYS = ["event_minute", "equipment_id", "site", "line"]

GOLD_COLUMNS = [
    "event_minute",
    "equipment_id",
    "site",
    "line",
    "event_count",
    "avg_temperature_c",
    "max_temperature_c",
    "avg_vibration_mm_s",
    "max_vibration_mm_s",
    "min_lubrication_pressure_bar",
    "avg_power_kw",
    "avg_anomaly_score",
    "anomaly_events",
    "quality_issue_events",
    "flow_missing_events",
    "warning_events",
    "critical_events",
    "avg_ingestion_latency_ms",
    "max_ingestion_latency_ms",
    "dominant_risk_level",
]

RISK_ORDER = {"normal": 0, "warning": 1, "critical": 2}


@dataclass
class GoldResult:
    input_rows: int = 0
    output_rows: int = 0
    malformed_rows_skipped: int = 0
    total_anomaly_events: int = 0
    total_warning_events: int = 0
    total_critical_events: int = 0


def load_silver_rows(input_path: str) -> list[dict[str, str]]:
    path = Path(input_path)
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8", newline="") as file_handle:
        return list(csv.DictReader(file_handle))


def build_gold_dataset(input_path: str, output_path: str, report_path: str) -> GoldResult:
    result = GoldResult()
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}

    for row in load_silver_rows(input_path):
        result.input_rows += 1
        try:
            normalized = normalize_silver_row(row)
        except (KeyError, TypeError, ValueError):
            result.malformed_rows_skipped += 1
            continue

        key = tuple(str(normalized[field]) for field in GROUP_KEYS)
        groups.setdefault(key, []).append(normalized)

    gold_rows = [summarize_group(rows) for rows in groups.values()]
    gold_rows.sort(key=lambda row: (row["event_minute"], row["equipment_id"], row["site"], row["line"]))

    result.output_rows = len(gold_rows)
    result.total_anomaly_events = sum(int(row["anomaly_events"]) for row in gold_rows)
    result.total_warning_events = sum(int(row["warning_events"]) for row in gold_rows)
    result.total_critical_events = sum(int(row["critical_events"]) for row in gold_rows)

    write_gold_csv(output_path, gold_rows)
    write_gold_report(report_path, result)
    return result


def normalize_silver_row(row: dict[str, str]) -> dict[str, Any]:
    return {
        "event_minute": row["event_minute"],
        "equipment_id": row["equipment_id"],
        "site": row["site"],
        "line": row["line"],
        "operational_state": row["operational_state"],
        "temperature_c": to_float(row["temperature_c"]),
        "vibration_mm_s": to_float(row["vibration_mm_s"]),
        "lubrication_pressure_bar": to_float(row["lubrication_pressure_bar"]),
        "power_kw": to_float(row["power_kw"]),
        "anomaly_score": to_float(row["anomaly_score"]),
        "ingestion_latency_ms": to_float(row["ingestion_latency_ms"]),
        "is_anomaly": to_bool(row["is_anomaly"]),
        "is_quality_issue": to_bool(row["is_quality_issue"]),
        "is_flow_missing": to_bool(row["is_flow_missing"]),
        "risk_level": row["risk_level"],
    }


def summarize_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    first = rows[0]
    risk_levels = [row["risk_level"] for row in rows]
    return {
        "event_minute": first["event_minute"],
        "equipment_id": first["equipment_id"],
        "site": first["site"],
        "line": first["line"],
        "event_count": len(rows),
        "avg_temperature_c": round(avg(row["temperature_c"] for row in rows), 2),
        "max_temperature_c": round(max(row["temperature_c"] for row in rows), 2),
        "avg_vibration_mm_s": round(avg(row["vibration_mm_s"] for row in rows), 2),
        "max_vibration_mm_s": round(max(row["vibration_mm_s"] for row in rows), 2),
        "min_lubrication_pressure_bar": round(min(row["lubrication_pressure_bar"] for row in rows), 2),
        "avg_power_kw": round(avg(row["power_kw"] for row in rows), 2),
        "avg_anomaly_score": round(avg(row["anomaly_score"] for row in rows), 3),
        "anomaly_events": sum(int(row["is_anomaly"]) for row in rows),
        "quality_issue_events": sum(int(row["is_quality_issue"]) for row in rows),
        "flow_missing_events": sum(int(row["is_flow_missing"]) for row in rows),
        "warning_events": sum(int(row["operational_state"] == "warning") for row in rows),
        "critical_events": sum(int(row["operational_state"] == "critical") for row in rows),
        "avg_ingestion_latency_ms": round(avg(row["ingestion_latency_ms"] for row in rows), 2),
        "max_ingestion_latency_ms": round(max(row["ingestion_latency_ms"] for row in rows), 2),
        "dominant_risk_level": max(risk_levels, key=lambda risk: RISK_ORDER.get(risk, 0)),
    }


def write_gold_csv(output_path: str, rows: list[dict[str, Any]]) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=GOLD_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def write_gold_report(output_path: str, result: GoldResult) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "input_rows": result.input_rows,
        "output_rows": result.output_rows,
        "malformed_rows_skipped": result.malformed_rows_skipped,
        "total_anomaly_events": result.total_anomaly_events,
        "total_warning_events": result.total_warning_events,
        "total_critical_events": result.total_critical_events,
    }
    with path.open("w", encoding="utf-8") as file_handle:
        json.dump(report, file_handle, indent=2)
        file_handle.write("\n")


def avg(values: Any) -> float:
    items = list(values)
    return sum(items) / len(items)


def to_float(value: str) -> float:
    return float(value)


def to_bool(value: str) -> bool:
    return value.lower() == "true"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the local gold equipment summary dataset.")
    parser.add_argument("--input", default=DEFAULT_SILVER_INPUT)
    parser.add_argument("--output", default=DEFAULT_GOLD_OUTPUT)
    parser.add_argument("--report", default=DEFAULT_GOLD_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_gold_dataset(args.input, args.output, args.report)
    print(
        "gold dataset built "
        f"input_rows={result.input_rows} "
        f"output_rows={result.output_rows} "
        f"malformed_rows_skipped={result.malformed_rows_skipped}"
    )


if __name__ == "__main__":
    main()
