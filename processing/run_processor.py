from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))

from batch.silver_transform import build_silver_dataset
from batch.gold_transform import build_gold_dataset

BRONZE_PATH = os.getenv("BRONZE_OUTPUT_PATH", "data/bronze/raw_telemetry.ndjson")
SILVER_OUTPUT = os.getenv("SILVER_OUTPUT_PATH", "data/silver/telemetry_clean.csv")
SILVER_REPORT = os.getenv("SILVER_REPORT_PATH", "data/silver/quality_report.json")
GOLD_OUTPUT = os.getenv("GOLD_SUMMARY_PATH", "data/gold/equipment_minute_summary.csv")
GOLD_REPORT = os.getenv("GOLD_REPORT_PATH", "data/gold/gold_quality_report.json")
INTERVAL = int(os.getenv("PROCESSOR_INTERVAL_SECONDS", "60"))


def run_once() -> None:
    silver = build_silver_dataset(BRONZE_PATH, SILVER_OUTPUT, SILVER_REPORT)
    print(
        f"silver built input={silver.input_records} output={silver.output_records} "
        f"anomalies={silver.anomaly_events} skipped={silver.malformed_records_skipped}",
        flush=True,
    )
    gold = build_gold_dataset(SILVER_OUTPUT, GOLD_OUTPUT, GOLD_REPORT)
    print(
        f"gold built input={gold.input_rows} output={gold.output_rows} "
        f"anomalies={gold.total_anomaly_events} skipped={gold.malformed_rows_skipped}",
        flush=True,
    )


if __name__ == "__main__":
    print(f"processor started interval={INTERVAL}s", flush=True)
    while True:
        try:
            run_once()
        except Exception as exc:
            print(f"processor error: {exc}", flush=True)
        time.sleep(INTERVAL)
