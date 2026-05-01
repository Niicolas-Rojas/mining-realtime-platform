from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Response
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST

from src.config import ApiConfig
from src.db import (
    fetch_active_alerts,
    fetch_operational_metrics,
    fetch_pipeline_metrics,
    fetch_recent_telemetry,
    fetch_telemetry_trends,
    wait_for_postgres,
)

# pipeline metrics
_g_accepted = Gauge("mining_events_accepted_total", "Total telemetry events accepted")
_g_rejected = Gauge("mining_events_rejected_total", "Total events dead-lettered")
_g_error_rate = Gauge("mining_error_rate", "Ingestion error rate (0 to 1)")
_g_events_per_min = Gauge("mining_events_per_minute", "Events accepted in the last minute")
_g_latency_ms = Gauge("mining_ingestion_latency_ms", "Average ingestion latency in milliseconds")

# equipment metrics (last 50 events window)
_g_temperature = Gauge("mining_avg_temperature_c", "Average temperature in Celsius")
_g_vibration = Gauge("mining_avg_vibration_mm_s", "Average vibration in mm/s")
_g_pressure = Gauge("mining_avg_pressure_bar", "Average lubrication pressure in bar")
_g_anomaly_score = Gauge("mining_avg_anomaly_score", "Average anomaly score (0 to 1)")
_g_anomaly_events = Gauge("mining_anomaly_events_window", "Events with non-ok quality flag")
_g_warning_events = Gauge("mining_warning_events_window", "Events in warning state")
_g_critical_events = Gauge("mining_critical_events_window", "Events in critical state")


config = ApiConfig()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    wait_for_postgres(config)
    yield


app = FastAPI(
    title="Mining Realtime Platform API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "api"}


@app.get("/api/v1/telemetry/recent")
def recent_telemetry(limit: int = Query(default=10, ge=1, le=100)) -> dict:
    records = fetch_recent_telemetry(config, limit=limit)
    return {"count": len(records), "items": records}


@app.get("/api/v1/metrics/summary")
def metrics_summary(window: int = Query(default=50, ge=5, le=500)) -> dict:
    metrics = fetch_operational_metrics(config, window=window)
    return {"window": window, "metrics": metrics}


@app.get("/api/v1/pipeline/metrics")
def pipeline_metrics() -> dict:
    metrics = fetch_pipeline_metrics(config)
    return {"metrics": metrics}


@app.get("/api/v1/alerts/active")
def active_alerts(limit: int = Query(default=20, ge=1, le=100)) -> dict:
    alerts = fetch_active_alerts(config, limit=limit)
    return {"count": len(alerts), "items": alerts}


@app.get("/api/v1/telemetry/trends")
def telemetry_trends(window: int = Query(default=60, ge=10, le=500)) -> dict:
    rows = fetch_telemetry_trends(config, window=window)
    return {"count": len(rows), "items": rows}


@app.get("/metrics")
def metrics() -> Response:
    try:
        pipeline = fetch_pipeline_metrics(config)
        _g_accepted.set(pipeline.get("accepted_events") or 0)
        _g_rejected.set(pipeline.get("invalid_events_dead_lettered") or 0)
        _g_error_rate.set(float(pipeline.get("ingestion_error_rate") or 0))
        _g_events_per_min.set(pipeline.get("events_ingested_per_minute") or 0)
        _g_latency_ms.set(float(pipeline.get("event_ingestion_latency_ms") or 0))

        ops = fetch_operational_metrics(config, window=50)
        _g_temperature.set(float(ops.get("avg_temperature_c") or 0))
        _g_vibration.set(float(ops.get("avg_vibration_mm_s") or 0))
        _g_pressure.set(float(ops.get("avg_lubrication_pressure_bar") or 0))
        _g_anomaly_score.set(float(ops.get("avg_anomaly_score") or 0))
        _g_anomaly_events.set(ops.get("non_ok_quality_events") or 0)
        _g_warning_events.set(ops.get("warning_events") or 0)
        _g_critical_events.set(ops.get("critical_events") or 0)
    except Exception:
        pass
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
