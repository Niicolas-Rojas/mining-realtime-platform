from __future__ import annotations

import time
from typing import Any

from psycopg import connect
from psycopg.rows import dict_row

from src.config import ApiConfig


def wait_for_postgres(config: ApiConfig, retries: int = 20, delay: float = 2.0) -> None:
    last_error: Exception | None = None
    for _attempt in range(1, retries + 1):
        try:
            with connect(config.postgres_dsn) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1;")
            return
        except Exception as exc:  # pragma: no cover - startup retry path
            last_error = exc
            time.sleep(delay)
    raise RuntimeError("could not connect to postgres") from last_error


def fetch_recent_telemetry(config: ApiConfig, limit: int = 10) -> list[dict[str, Any]]:
    sql = """
    SELECT
        id,
        event_id,
        equipment_id,
        site,
        line,
        operational_state,
        event_ts,
        ingested_at,
        payload
    FROM raw_telemetry
    ORDER BY id DESC
    LIMIT %s;
    """
    with connect(config.postgres_dsn, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (limit,))
            rows = cursor.fetchall()
    return list(rows)


def fetch_operational_metrics(config: ApiConfig, window: int = 50) -> dict[str, Any]:
    sql = """
    WITH recent AS (
        SELECT *
        FROM raw_telemetry
        ORDER BY id DESC
        LIMIT %s
    ),
    latest AS (
        SELECT operational_state, event_ts
        FROM recent
        ORDER BY id DESC
        LIMIT 1
    )
    SELECT
        (SELECT COUNT(*) FROM raw_telemetry) AS total_events,
        COUNT(*) AS window_events,
        ROUND(AVG((payload->>'temperature_c')::numeric), 2) AS avg_temperature_c,
        ROUND(MAX((payload->>'temperature_c')::numeric), 2) AS max_temperature_c,
        ROUND(AVG((payload->>'vibration_mm_s')::numeric), 2) AS avg_vibration_mm_s,
        ROUND(AVG((payload->>'lubrication_pressure_bar')::numeric), 2) AS avg_lubrication_pressure_bar,
        ROUND(AVG((payload->>'anomaly_score')::numeric), 3) AS avg_anomaly_score,
        ROUND(AVG(EXTRACT(EPOCH FROM (ingested_at - event_ts)) * 1000), 2) AS avg_ingestion_latency_ms,
        ROUND(MAX(EXTRACT(EPOCH FROM (ingested_at - event_ts)) * 1000), 2) AS max_ingestion_latency_ms,
        COUNT(*) FILTER (WHERE operational_state = 'warning') AS warning_events,
        COUNT(*) FILTER (WHERE operational_state = 'critical') AS critical_events,
        COUNT(*) FILTER (WHERE payload->>'quality_flag' <> 'ok') AS non_ok_quality_events,
        (SELECT operational_state FROM latest) AS latest_operational_state,
        (SELECT event_ts FROM latest) AS latest_event_ts
    FROM recent;
    """
    with connect(config.postgres_dsn, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (window,))
            row = cursor.fetchone()
    return dict(row) if row else {}


def fetch_pipeline_metrics(config: ApiConfig) -> dict[str, Any]:
    sql = """
    WITH accepted AS (
        SELECT
            COUNT(*) AS accepted_events,
            COUNT(*) FILTER (WHERE ingested_at >= NOW() - INTERVAL '1 minute')
                AS events_ingested_last_minute,
            ROUND(AVG(EXTRACT(EPOCH FROM (ingested_at - event_ts)) * 1000), 2)
                AS avg_ingestion_latency_ms,
            ROUND(MAX(EXTRACT(EPOCH FROM (ingested_at - event_ts)) * 1000), 2)
                AS max_ingestion_latency_ms,
            MAX(ingested_at) AS latest_accepted_at
        FROM raw_telemetry
    ),
    rejected AS (
        SELECT
            COUNT(*) AS rejected_events,
            COUNT(*) FILTER (WHERE rejected_at >= NOW() - INTERVAL '1 minute')
                AS rejected_events_last_minute,
            MAX(rejected_at) AS latest_rejected_at
        FROM rejected_telemetry
    )
    SELECT
        accepted.accepted_events,
        rejected.rejected_events AS invalid_events_dead_lettered,
        accepted.accepted_events + rejected.rejected_events AS total_messages_seen,
        accepted.events_ingested_last_minute AS events_ingested_per_minute,
        rejected.rejected_events_last_minute AS invalid_events_last_minute,
        CASE
            WHEN accepted.accepted_events + rejected.rejected_events = 0 THEN 0
            ELSE ROUND(
                rejected.rejected_events::numeric
                / (accepted.accepted_events + rejected.rejected_events),
                4
            )
        END AS ingestion_error_rate,
        accepted.avg_ingestion_latency_ms AS event_ingestion_latency_ms,
        accepted.max_ingestion_latency_ms AS max_ingestion_latency_ms,
        accepted.latest_accepted_at,
        rejected.latest_rejected_at
    FROM accepted, rejected;
    """
    with connect(config.postgres_dsn, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            row = cursor.fetchone()
    return dict(row) if row else {}


def fetch_active_alerts(config: ApiConfig, limit: int = 20) -> list[dict[str, Any]]:
    sql = """
    WITH recent AS (
        SELECT
            id,
            event_id,
            equipment_id,
            site,
            line,
            operational_state,
            event_ts,
            ingested_at,
            payload,
            (payload->>'temperature_c')::numeric AS temperature_c,
            (payload->>'vibration_mm_s')::numeric AS vibration_mm_s,
            (payload->>'lubrication_pressure_bar')::numeric AS lubrication_pressure_bar,
            (payload->>'anomaly_score')::numeric AS anomaly_score,
            payload->>'quality_flag' AS quality_flag
        FROM raw_telemetry
        ORDER BY id DESC
        LIMIT 500
    )
    SELECT
        id,
        event_id,
        equipment_id,
        site,
        line,
        event_ts,
        ingested_at,
        operational_state,
        temperature_c,
        vibration_mm_s,
        lubrication_pressure_bar,
        anomaly_score,
        quality_flag,
        CASE
            WHEN operational_state = 'critical' OR temperature_c >= 82 OR lubrication_pressure_bar < 2.2
                THEN 'critical'
            ELSE 'warning'
        END AS alert_severity,
        CASE
            WHEN operational_state = 'critical' OR temperature_c >= 82
                THEN 'High temperature risk'
            WHEN lubrication_pressure_bar < 2.8
                THEN 'Low lubrication pressure'
            WHEN vibration_mm_s >= 4.5
                THEN 'High vibration detected'
            WHEN anomaly_score >= 0.7
                THEN 'Elevated anomaly score'
            WHEN quality_flag <> 'ok'
                THEN 'Sensor data quality issue'
            ELSE 'Operational warning state'
        END AS alert_reason
    FROM recent
    WHERE
        operational_state IN ('warning', 'critical')
        OR temperature_c >= 78
        OR vibration_mm_s >= 4.5
        OR lubrication_pressure_bar < 2.8
        OR anomaly_score >= 0.7
        OR quality_flag <> 'ok'
    ORDER BY id DESC
    LIMIT %s;
    """
    with connect(config.postgres_dsn, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (limit,))
            rows = cursor.fetchall()
    return list(rows)


def fetch_telemetry_trends(config: ApiConfig, window: int = 60) -> list[dict[str, Any]]:
    sql = """
    WITH recent AS (
        SELECT
            id,
            event_ts,
            ingested_at,
            operational_state,
            (payload->>'temperature_c')::numeric AS temperature_c,
            (payload->>'vibration_mm_s')::numeric AS vibration_mm_s,
            (payload->>'lubrication_pressure_bar')::numeric AS lubrication_pressure_bar,
            (payload->>'power_kw')::numeric AS power_kw,
            (payload->>'anomaly_score')::numeric AS anomaly_score,
            ROUND(EXTRACT(EPOCH FROM (ingested_at - event_ts)) * 1000, 2) AS ingestion_latency_ms
        FROM raw_telemetry
        ORDER BY id DESC
        LIMIT %s
    )
    SELECT
        event_ts,
        ingested_at,
        operational_state,
        temperature_c,
        vibration_mm_s,
        lubrication_pressure_bar,
        power_kw,
        anomaly_score,
        ingestion_latency_ms
    FROM recent
    ORDER BY event_ts ASC;
    """
    with connect(config.postgres_dsn, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (window,))
            rows = cursor.fetchall()
    return list(rows)
