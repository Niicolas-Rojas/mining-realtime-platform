from __future__ import annotations

import os
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from psycopg import Connection


CREATE_GOLD_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS gold_summary (
    id BIGSERIAL PRIMARY KEY,
    event_minute TIMESTAMPTZ NOT NULL,
    equipment_id TEXT NOT NULL,
    site TEXT NOT NULL,
    line TEXT NOT NULL,
    event_count INTEGER,
    avg_temperature_c FLOAT,
    max_temperature_c FLOAT,
    avg_vibration_mm_s FLOAT,
    max_vibration_mm_s FLOAT,
    min_lubrication_pressure_bar FLOAT,
    avg_power_kw FLOAT,
    avg_anomaly_score FLOAT,
    anomaly_events INTEGER,
    quality_issue_events INTEGER,
    flow_missing_events INTEGER,
    warning_events INTEGER,
    critical_events INTEGER,
    avg_ingestion_latency_ms FLOAT,
    max_ingestion_latency_ms FLOAT,
    dominant_risk_level TEXT,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (event_minute, equipment_id)
);
CREATE INDEX IF NOT EXISTS idx_gold_summary_event_minute
    ON gold_summary (event_minute DESC);
"""

UPSERT_GOLD_SQL = """
INSERT INTO gold_summary (
    event_minute, equipment_id, site, line, event_count,
    avg_temperature_c, max_temperature_c,
    avg_vibration_mm_s, max_vibration_mm_s,
    min_lubrication_pressure_bar, avg_power_kw, avg_anomaly_score,
    anomaly_events, quality_issue_events, flow_missing_events,
    warning_events, critical_events,
    avg_ingestion_latency_ms, max_ingestion_latency_ms,
    dominant_risk_level
) VALUES (
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (event_minute, equipment_id) DO UPDATE SET
    event_count = EXCLUDED.event_count,
    avg_temperature_c = EXCLUDED.avg_temperature_c,
    max_temperature_c = EXCLUDED.max_temperature_c,
    avg_vibration_mm_s = EXCLUDED.avg_vibration_mm_s,
    max_vibration_mm_s = EXCLUDED.max_vibration_mm_s,
    min_lubrication_pressure_bar = EXCLUDED.min_lubrication_pressure_bar,
    avg_power_kw = EXCLUDED.avg_power_kw,
    avg_anomaly_score = EXCLUDED.avg_anomaly_score,
    anomaly_events = EXCLUDED.anomaly_events,
    quality_issue_events = EXCLUDED.quality_issue_events,
    flow_missing_events = EXCLUDED.flow_missing_events,
    warning_events = EXCLUDED.warning_events,
    critical_events = EXCLUDED.critical_events,
    avg_ingestion_latency_ms = EXCLUDED.avg_ingestion_latency_ms,
    max_ingestion_latency_ms = EXCLUDED.max_ingestion_latency_ms,
    dominant_risk_level = EXCLUDED.dominant_risk_level,
    processed_at = NOW();
"""


def build_postgres_dsn() -> str:
    db = os.getenv("POSTGRES_DB", "mining_rt")
    user = os.getenv("POSTGRES_USER", "mining")
    password = os.getenv("POSTGRES_PASSWORD", "mining123")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    sslmode = os.getenv("POSTGRES_SSLMODE", "")
    dsn = f"dbname={db} user={user} password={password} host={host} port={port}"
    if sslmode:
        dsn += f" sslmode={sslmode}"
    return dsn


def ensure_gold_schema(connection: "Connection") -> None:
    with connection.cursor() as cursor:
        cursor.execute(CREATE_GOLD_TABLE_SQL)
    connection.commit()


def write_gold_rows(connection: "Connection", rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    with connection.cursor() as cursor:
        for row in rows:
            cursor.execute(
                UPSERT_GOLD_SQL,
                (
                    row["event_minute"],
                    row["equipment_id"],
                    row["site"],
                    row["line"],
                    row["event_count"],
                    row["avg_temperature_c"],
                    row["max_temperature_c"],
                    row["avg_vibration_mm_s"],
                    row["max_vibration_mm_s"],
                    row["min_lubrication_pressure_bar"],
                    row["avg_power_kw"],
                    row["avg_anomaly_score"],
                    row["anomaly_events"],
                    row["quality_issue_events"],
                    row["flow_missing_events"],
                    row["warning_events"],
                    row["critical_events"],
                    row["avg_ingestion_latency_ms"],
                    row["max_ingestion_latency_ms"],
                    row["dominant_risk_level"],
                ),
            )
    connection.commit()
    return len(rows)
