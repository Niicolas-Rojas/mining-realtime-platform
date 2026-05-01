from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))

from batch.silver_transform import build_silver_dataset
from batch.gold_transform import build_gold_dataset, load_gold_rows
from batch.pg_storage import build_postgres_dsn, ensure_gold_schema, write_gold_rows

BRONZE_PATH = os.getenv("BRONZE_OUTPUT_PATH", "data/bronze/raw_telemetry.ndjson")
SILVER_OUTPUT = os.getenv("SILVER_OUTPUT_PATH", "data/silver/telemetry_clean.csv")
SILVER_REPORT = os.getenv("SILVER_REPORT_PATH", "data/silver/quality_report.json")
GOLD_OUTPUT = os.getenv("GOLD_SUMMARY_PATH", "data/gold/equipment_minute_summary.csv")
GOLD_REPORT = os.getenv("GOLD_REPORT_PATH", "data/gold/gold_quality_report.json")
INTERVAL = int(os.getenv("PROCESSOR_INTERVAL_SECONDS", "60"))
PG_ENABLED = os.getenv("POSTGRES_HOST", "") != ""


def connect_postgres():
    from psycopg import connect
    dsn = build_postgres_dsn()
    for attempt in range(1, 11):
        try:
            conn = connect(dsn)
            ensure_gold_schema(conn)
            print(f"processor connected to postgres on attempt={attempt}", flush=True)
            return conn
        except Exception as exc:
            print(f"processor postgres not ready attempt={attempt} error={exc}", flush=True)
            time.sleep(3)
    return None


def run_once(pg_conn) -> None:
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

    if pg_conn is not None:
        try:
            gold_rows = load_gold_rows(GOLD_OUTPUT)
            written = write_gold_rows(pg_conn, gold_rows)
            print(f"gold written to postgres rows={written}", flush=True)
        except Exception as exc:
            print(f"processor postgres write error: {exc}", flush=True)


if __name__ == "__main__":
    pg_conn = connect_postgres() if PG_ENABLED else None
    if not PG_ENABLED:
        print("processor started without postgres (POSTGRES_HOST not set)", flush=True)
    print(f"processor started interval={INTERVAL}s", flush=True)
    while True:
        try:
            run_once(pg_conn)
        except Exception as exc:
            print(f"processor error: {exc}", flush=True)
        time.sleep(INTERVAL)
