from __future__ import annotations

import csv
from datetime import datetime
import html
import json
import os
from pathlib import Path
import time
from typing import Any

import altair as alt
import pandas as pd
import requests
import streamlit as st


def _resolve_api_url() -> str:
    try:
        return st.secrets["API_BASE_URL"].rstrip("/")
    except Exception:
        return os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

API_BASE_URL = _resolve_api_url()
GOLD_SUMMARY_PATH = os.getenv("GOLD_SUMMARY_PATH", "data/gold/equipment_minute_summary.csv")
GOLD_REPORT_PATH = os.getenv("GOLD_REPORT_PATH", "data/gold/gold_quality_report.json")

TEMP_WARNING_C = 78.0
TEMP_CRITICAL_C = 82.0
VIBRATION_WARNING_MM_S = 4.5
VIBRATION_CRITICAL_MM_S = 4.8
PRESSURE_WARNING_BAR = 2.8
PRESSURE_CRITICAL_BAR = 2.2
ANOMALY_WARNING_SCORE = 0.7

COLOR_GREEN = "#16724f"
COLOR_AMBER = "#b86b14"
COLOR_RED = "#b42318"
COLOR_STEEL = "#36556d"
COLOR_BLUE = "#2563eb"
COLOR_PURPLE = "#7c3aed"
COLOR_MUTED = "#667085"

STATE_COLOR_DOMAIN = ["running", "warning", "critical", "stopped", "maintenance"]
STATE_COLOR_RANGE = [COLOR_GREEN, COLOR_AMBER, COLOR_RED, "#475467", "#0f766e"]
RISK_COLOR_DOMAIN = ["normal", "warning", "critical", "n/a"]
RISK_COLOR_RANGE = [COLOR_GREEN, COLOR_AMBER, COLOR_RED, COLOR_MUTED]

API_ERRORS: list[str] = []


def fetch_json(path: str, params: dict[str, Any] | None = None, default: dict[str, Any] | None = None) -> dict[str, Any]:
    fallback = default if default is not None else {}
    try:
        response = requests.get(f"{API_BASE_URL}{path}", params=params, timeout=4)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        API_ERRORS.append(f"{path}: {exc}")
        return fallback


@st.cache_data(ttl=30)
def load_gold_summary(path: str) -> list[dict[str, Any]]:
    # Try API first (needed for Streamlit Cloud where local files are unavailable)
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/gold/summary", params={"limit": 500}, timeout=4)
        if response.status_code == 200:
            items = response.json().get("items", [])
            if items:
                return [normalize_gold_row(row) for row in items]
    except Exception:
        pass
    # Fall back to local CSV
    target = Path(path)
    if not target.exists():
        return []
    with target.open("r", encoding="utf-8", newline="") as file_handle:
        return [normalize_gold_row(row) for row in csv.DictReader(file_handle)]


@st.cache_data(ttl=30)
def load_gold_report(path: str) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return {}
    with target.open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def normalize_gold_row(row: dict[str, Any]) -> dict[str, Any]:
    numeric_fields = {
        "event_count": int,
        "avg_temperature_c": float,
        "max_temperature_c": float,
        "avg_vibration_mm_s": float,
        "max_vibration_mm_s": float,
        "min_lubrication_pressure_bar": float,
        "avg_power_kw": float,
        "avg_anomaly_score": float,
        "anomaly_events": int,
        "quality_issue_events": int,
        "flow_missing_events": int,
        "warning_events": int,
        "critical_events": int,
        "avg_ingestion_latency_ms": float,
        "max_ingestion_latency_ms": float,
    }
    normalized: dict[str, Any] = dict(row)
    for field, caster in numeric_fields.items():
        if field in normalized and normalized[field] is not None:
            normalized[field] = caster(normalized[field])
    return normalized


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def fmt_number(value: Any, digits: int = 2) -> str:
    if value in (None, ""):
        return "n/a"
    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def fmt_compact(value: Any, digits: int = 2) -> str:
    if value in (None, ""):
        return "n/a"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(number) >= 1000:
        return f"{number:,.0f}"
    return f"{number:.{digits}f}"


def parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def fmt_timestamp(value: Any) -> str:
    parsed = parse_timestamp(value)
    if parsed is None:
        return "n/a" if not value else str(value)
    return parsed.strftime("%Y-%m-%d %H:%M:%S UTC")


def esc(value: Any) -> str:
    return html.escape(str(value))


def severity_color(severity: str) -> str:
    if severity == "critical":
        return COLOR_RED
    return COLOR_AMBER


def risk_badge(metrics: dict[str, Any], alerts: list[dict[str, Any]], api_online: bool) -> tuple[str, str, str]:
    if not api_online:
        return (
            "Sin senal API",
            COLOR_MUTED,
            "La vista historica sigue disponible; levanta el stack para ver la operacion viva.",
        )

    criticals = sum(1 for alert in alerts if alert.get("alert_severity") == "critical")
    criticals += to_int(metrics.get("critical_events", 0))
    warnings = sum(1 for alert in alerts if alert.get("alert_severity") == "warning")
    warnings += to_int(metrics.get("warning_events", 0))
    anomaly = to_float(metrics.get("avg_anomaly_score", 0))
    temp = to_float(metrics.get("max_temperature_c", 0))
    pressure = to_float(metrics.get("avg_lubrication_pressure_bar", 99))

    if criticals > 0 or temp >= TEMP_CRITICAL_C or pressure < PRESSURE_CRITICAL_BAR:
        return "Critico", "#7f1d1d", "Requiere atencion operacional inmediata."
    if warnings > 0 or anomaly >= 0.65 or temp >= TEMP_WARNING_C or pressure < PRESSURE_WARNING_BAR:
        return "Advertencia", "#92400e", "Las condiciones se estan desviando del rango normal."
    return "Estable", "#166534", "La telemetria se mantiene dentro del rango esperado."


def latest_critical_alert(alerts: list[dict[str, Any]]) -> dict[str, Any] | None:
    for alert in alerts:
        if alert.get("alert_severity") == "critical":
            return alert
    return None


def latency_ms(row: dict[str, Any]) -> float | None:
    ingested_at = parse_timestamp(row.get("ingested_at"))
    event_ts = parse_timestamp(row.get("event_ts"))
    if ingested_at is None or event_ts is None:
        return None
    return round((ingested_at - event_ts).total_seconds() * 1000, 2)


def status_variant(state: str) -> str:
    if state == "critical":
        return "status-critical"
    if state == "warning":
        return "status-warning"
    return "status-running"


def translate_state(state: str | None) -> str:
    translations = {
        "running": "operando",
        "warning": "advertencia",
        "critical": "critico",
        "stopped": "detenido",
        "maintenance": "mantencion",
    }
    if state is None:
        return "n/d"
    return translations.get(state, state)


def translate_risk(risk_level: str | None) -> str:
    translations = {
        "normal": "normal",
        "warning": "advertencia",
        "critical": "critico",
        "n/a": "n/d",
    }
    if risk_level is None:
        return "n/d"
    return translations.get(risk_level, risk_level)


def translate_alert_reason(reason: str | None) -> str:
    translations = {
        "High temperature risk": "Riesgo por alta temperatura",
        "Low lubrication pressure": "Baja presion de lubricacion",
        "High vibration detected": "Alta vibracion detectada",
        "Elevated anomaly score": "Puntaje de anomalia elevado",
        "Sensor data quality issue": "Problema de calidad del dato del sensor",
        "Operational warning state": "Estado operacional en advertencia",
    }
    if reason is None:
        return "Sin motivo informado"
    return translations.get(reason, reason)


def translate_quality_flag(flag: str | None) -> str:
    translations = {
        "ok": "correcta",
        "partial": "parcial",
        "anomalous": "anomala",
    }
    if flag is None:
        return "n/d"
    return translations.get(flag, flag)


def translate_service_status(status: str | None) -> str:
    if status == "ok":
        return "operativa"
    if not status:
        return "sin senal"
    return status


def summarize_gold(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "window_count": 0,
            "event_count": 0,
            "anomaly_events": 0,
            "warning_events": 0,
            "critical_events": 0,
            "avg_temperature_c": None,
            "max_temperature_c": None,
            "avg_vibration_mm_s": None,
            "min_lubrication_pressure_bar": None,
            "avg_latency_ms": None,
            "dominant_risk_level": "n/a",
        }
    event_count = sum(row["event_count"] for row in rows)
    risk_order = {"normal": 0, "warning": 1, "critical": 2}
    return {
        "window_count": len(rows),
        "event_count": event_count,
        "anomaly_events": sum(row["anomaly_events"] for row in rows),
        "warning_events": sum(row["warning_events"] for row in rows),
        "critical_events": sum(row["critical_events"] for row in rows),
        "avg_temperature_c": weighted_avg(rows, "avg_temperature_c", "event_count"),
        "max_temperature_c": max(row["max_temperature_c"] for row in rows),
        "avg_vibration_mm_s": weighted_avg(rows, "avg_vibration_mm_s", "event_count"),
        "min_lubrication_pressure_bar": min(row["min_lubrication_pressure_bar"] for row in rows),
        "avg_latency_ms": weighted_avg(rows, "avg_ingestion_latency_ms", "event_count"),
        "dominant_risk_level": max(rows, key=lambda row: risk_order.get(row["dominant_risk_level"], 0))[
            "dominant_risk_level"
        ],
    }


def weighted_avg(rows: list[dict[str, Any]], value_field: str, weight_field: str) -> float:
    total_weight = sum(row[weight_field] for row in rows)
    if total_weight == 0:
        return 0.0
    return round(sum(row[value_field] * row[weight_field] for row in rows) / total_weight, 2)


def build_trends_df(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["event_ts"] = pd.to_datetime(df["event_ts"], errors="coerce", utc=True)
    for field in [
        "temperature_c",
        "vibration_mm_s",
        "lubrication_pressure_bar",
        "power_kw",
        "anomaly_score",
        "ingestion_latency_ms",
    ]:
        if field in df:
            df[field] = pd.to_numeric(df[field], errors="coerce")
    df["estado"] = df["operational_state"].map(translate_state)
    df["state_level"] = df["operational_state"].map({"running": 0, "warning": 1, "critical": 2}).fillna(0)
    return df.dropna(subset=["event_ts"])


def build_alerts_df(alerts: list[dict[str, Any]]) -> pd.DataFrame:
    if not alerts:
        return pd.DataFrame()

    df = pd.DataFrame(alerts)
    df["motivo"] = df["alert_reason"].map(translate_alert_reason)
    df["severidad"] = df["alert_severity"].map(translate_state)
    for field in ["temperature_c", "vibration_mm_s", "lubrication_pressure_bar", "anomaly_score"]:
        if field in df:
            df[field] = pd.to_numeric(df[field], errors="coerce")
    return df


def build_recent_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    table_rows = []
    for row in rows:
        payload = row.get("payload") or {}
        table_rows.append(
            {
                "timestamp_evento": fmt_timestamp(row.get("event_ts")),
                "equipo": row.get("equipment_id", "n/a"),
                "estado": translate_state(row.get("operational_state")),
                "temperatura_c": payload.get("temperature_c"),
                "vibracion_mm_s": payload.get("vibration_mm_s"),
                "presion_bar": payload.get("lubrication_pressure_bar"),
                "potencia_kw": payload.get("power_kw"),
                "anomalia": payload.get("anomaly_score"),
                "calidad": translate_quality_flag(payload.get("quality_flag")),
                "latencia_ms": latency_ms(row),
            }
        )
    return table_rows


def build_gold_df(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["event_minute"] = pd.to_datetime(df["event_minute"], errors="coerce", utc=True)
    df["riesgo"] = df["dominant_risk_level"].map(translate_risk)
    numeric_fields = [
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
    ]
    for field in numeric_fields:
        df[field] = pd.to_numeric(df[field], errors="coerce")
    return df.dropna(subset=["event_minute"])


def alt_values(rows: list[dict[str, Any]]) -> alt.Data:
    return alt.Data(values=rows)


def alt_records(df: pd.DataFrame) -> alt.Data:
    prepared = df.copy()
    for column in prepared.columns:
        if pd.api.types.is_datetime64_any_dtype(prepared[column]):
            prepared[column] = prepared[column].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    prepared = prepared.astype(object).where(pd.notnull(prepared), None)
    return alt_values(prepared.to_dict(orient="records"))


def style_chart(chart: alt.Chart) -> alt.Chart:
    return (
        chart.configure_axis(
            gridColor="#e4e7ec",
            gridOpacity=0.7,
            labelColor="#667085",
            titleColor="#344054",
            labelFont="Instrument Sans",
            titleFont="Instrument Sans",
            labelFontSize=11,
            titleFontSize=11,
            titlePadding=8,
            tickColor="#e4e7ec",
        )
        .configure_title(
            font="Instrument Sans",
            fontSize=13,
            fontWeight=600,
            color="#344054",
            anchor="start",
            offset=12,
        )
        .configure_header(
            labelColor="#344054",
            titleColor="#344054",
            labelFont="Instrument Sans",
            titleFont="Instrument Sans",
            labelFontSize=11,
        )
        .configure_legend(
            labelColor="#475467",
            titleColor="#344054",
            labelFont="Instrument Sans",
            titleFont="Instrument Sans",
            labelFontSize=11,
            titleFontSize=11,
            orient="bottom",
            padding=6,
        )
        .configure_view(strokeWidth=0, fill="#ffffff", fillOpacity=0)
    )


def render_metric_chart(
    df: pd.DataFrame,
    field: str,
    title: str,
    unit: str,
    color: str,
    warning: float | None = None,
    critical: float | None = None,
    y_domain: tuple[float, float] | None = None,
) -> None:
    if df.empty or field not in df or df[field].dropna().empty:
        st.info("Sin datos suficientes para esta senal.")
        return

    y_scale = alt.Scale(domain=list(y_domain)) if y_domain else alt.Scale(zero=False, padding=8)

    base = alt.Chart(alt_records(df)).encode(
        x=alt.X("event_ts:T", title=None, axis=alt.Axis(format="%H:%M", labelAngle=0, tickCount=8)),
        tooltip=[
            alt.Tooltip("event_ts:T", title="timestamp", format="%H:%M:%S"),
            alt.Tooltip(f"{field}:Q", title=f"{title} ({unit})", format=".2f"),
            alt.Tooltip("estado:N", title="estado"),
        ],
    )
    area = base.mark_area(color=color, opacity=0.13).encode(
        y=alt.Y(f"{field}:Q", title=f"{unit}", scale=y_scale)
    )
    line = base.mark_line(color=color, strokeWidth=2.8).encode(
        y=alt.Y(f"{field}:Q", title=f"{unit}", scale=y_scale)
    )
    points = base.mark_circle(size=65, opacity=0.88).encode(
        y=alt.Y(f"{field}:Q", title=f"{unit}", scale=y_scale),
        color=alt.Color(
            "operational_state:N",
            title="estado",
            scale=alt.Scale(domain=STATE_COLOR_DOMAIN, range=STATE_COLOR_RANGE),
        ),
    )

    layers: list[alt.Chart] = [area, line, points]
    threshold_rows = []
    if warning is not None:
        threshold_rows.append({"limite": warning, "tipo": "advertencia"})
    if critical is not None:
        threshold_rows.append({"limite": critical, "tipo": "critico"})
    if threshold_rows:
        rules = (
            alt.Chart(alt_values(threshold_rows))
            .mark_rule(strokeDash=[6, 4], strokeWidth=1.6)
            .encode(
                y="limite:Q",
                color=alt.Color(
                    "tipo:N",
                    title="umbral",
                    scale=alt.Scale(domain=["advertencia", "critico"], range=[COLOR_AMBER, COLOR_RED]),
                ),
            )
        )
        layers.append(rules)

    chart = alt.layer(*layers).properties(height=280, title=title)
    st.altair_chart(style_chart(chart), use_container_width=True)


def render_anomaly_chart(df: pd.DataFrame) -> None:
    if df.empty or "anomaly_score" not in df or df["anomaly_score"].dropna().empty:
        st.info("Sin datos suficientes para calcular anomalias.")
        return

    base = alt.Chart(alt_records(df)).encode(
        x=alt.X("event_ts:T", title=None, axis=alt.Axis(format="%H:%M", labelAngle=0)),
        tooltip=[
            alt.Tooltip("event_ts:T", title="timestamp", format="%H:%M:%S"),
            alt.Tooltip("anomaly_score:Q", title="anomalia", format=".3f"),
            alt.Tooltip("estado:N", title="estado"),
        ],
    )
    area = base.mark_area(color=COLOR_RED, opacity=0.08).encode(
        y=alt.Y("anomaly_score:Q", title="puntaje", scale=alt.Scale(domain=[0, 1]))
    )
    line = base.mark_line(color=COLOR_RED, strokeWidth=2.5).encode(
        y=alt.Y("anomaly_score:Q", title="puntaje", scale=alt.Scale(domain=[0, 1]))
    )
    points = base.mark_circle(size=55, opacity=0.85).encode(
        y=alt.Y("anomaly_score:Q", title="puntaje", scale=alt.Scale(domain=[0, 1])),
        color=alt.Color(
            "operational_state:N",
            title="estado",
            scale=alt.Scale(domain=STATE_COLOR_DOMAIN, range=STATE_COLOR_RANGE),
        ),
    )
    threshold = alt.Chart(alt_values([{"limite": ANOMALY_WARNING_SCORE, "tipo": "advertencia"}])).mark_rule(
        strokeDash=[5, 4], strokeWidth=1.3, color=COLOR_AMBER
    ).encode(y="limite:Q")

    chart = alt.layer(area, line, points, threshold).properties(height=280, title="Puntaje de anomalia")
    st.altair_chart(style_chart(chart), use_container_width=True)


def render_state_timeline(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("Sin estados recientes para graficar.")
        return

    chart = (
        alt.Chart(alt_records(df))
        .mark_circle(size=88, opacity=0.9)
        .encode(
            x=alt.X("event_ts:T", title=None, axis=alt.Axis(format="%H:%M", labelAngle=0, tickCount=8)),
            y=alt.Y(
                "state_level:Q",
                title="estado",
                scale=alt.Scale(domain=[-0.3, 2.3]),
                axis=alt.Axis(values=[0, 1, 2], labelExpr="datum.value == 0 ? 'operando' : datum.value == 1 ? 'advertencia' : 'critico'"),
            ),
            color=alt.Color(
                "operational_state:N",
                title="estado",
                scale=alt.Scale(domain=STATE_COLOR_DOMAIN, range=STATE_COLOR_RANGE),
            ),
            tooltip=[
                alt.Tooltip("event_ts:T", title="timestamp", format="%H:%M:%S"),
                alt.Tooltip("estado:N", title="estado"),
                alt.Tooltip("temperature_c:Q", title="temp C", format=".2f"),
                alt.Tooltip("vibration_mm_s:Q", title="vibracion", format=".2f"),
                alt.Tooltip("lubrication_pressure_bar:Q", title="presion", format=".2f"),
            ],
        )
        .properties(height=265, title="Linea de estado operacional")
    )
    st.altair_chart(style_chart(chart), use_container_width=True)


def render_state_distribution(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("Sin distribucion de estados.")
        return

    counts = (
        df.groupby(["operational_state", "estado"], dropna=False)
        .size()
        .reset_index(name="eventos")
        .sort_values("eventos", ascending=False)
    )
    chart = (
        alt.Chart(alt_records(counts))
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X("eventos:Q", title="eventos"),
            y=alt.Y("estado:N", title=None, sort="-x"),
            color=alt.Color(
                "operational_state:N",
                title="estado",
                scale=alt.Scale(domain=STATE_COLOR_DOMAIN, range=STATE_COLOR_RANGE),
            ),
            tooltip=[
                alt.Tooltip("estado:N", title="estado"),
                alt.Tooltip("eventos:Q", title="eventos"),
            ],
        )
        .properties(height=230, title="Composicion de la ventana")
    )
    st.altair_chart(style_chart(chart), use_container_width=True)


def render_alert_reason_chart(alerts_df: pd.DataFrame) -> None:
    if alerts_df.empty:
        st.info("Sin alertas activas en esta ventana.")
        return

    counts = alerts_df.groupby(["motivo", "alert_severity"], dropna=False).size().reset_index(name="eventos")
    chart = (
        alt.Chart(alt_records(counts))
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X("eventos:Q", title="eventos"),
            y=alt.Y("motivo:N", title=None, sort="-x"),
            color=alt.Color(
                "alert_severity:N",
                title="severidad",
                scale=alt.Scale(domain=["warning", "critical"], range=[COLOR_AMBER, COLOR_RED]),
            ),
            tooltip=[
                alt.Tooltip("motivo:N", title="motivo"),
                alt.Tooltip("alert_severity:N", title="severidad"),
                alt.Tooltip("eventos:Q", title="eventos"),
            ],
        )
        .properties(height=max(220, min(400, 52 * len(counts))), title="Que explica las alertas")
    )
    st.altair_chart(style_chart(chart), use_container_width=True)


def render_pipeline_quality_chart(metrics: dict[str, Any]) -> None:
    accepted = to_int(metrics.get("accepted_events", 0))
    rejected = to_int(metrics.get("invalid_events_dead_lettered", 0))
    total = accepted + rejected
    if total == 0:
        st.info("Sin mensajes observados por el pipeline.")
        return

    data = [
        {"tipo": "aceptados", "mensajes": accepted, "pct": round(accepted / total * 100, 1)},
        {"tipo": "rechazados", "mensajes": rejected, "pct": round(rejected / total * 100, 1)},
    ]
    chart = (
        alt.Chart(alt_values(data))
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X("mensajes:Q", title="mensajes", axis=alt.Axis(format=",")),
            y=alt.Y("tipo:N", title=None, sort=["aceptados", "rechazados"]),
            color=alt.Color(
                "tipo:N",
                title="resultado",
                scale=alt.Scale(domain=["aceptados", "rechazados"], range=[COLOR_GREEN, COLOR_RED]),
            ),
            tooltip=[
                alt.Tooltip("tipo:N", title="resultado"),
                alt.Tooltip("mensajes:Q", title="mensajes", format=","),
                alt.Tooltip("pct:Q", title="%", format=".1f"),
            ],
        )
        .properties(height=110, title="Calidad de mensajes")
    )
    st.altair_chart(style_chart(chart), use_container_width=True)


def render_latency_chart(df: pd.DataFrame) -> None:
    if df.empty or "ingestion_latency_ms" not in df or df["ingestion_latency_ms"].dropna().empty:
        st.info("Sin latencia reciente para graficar.")
        return

    base = alt.Chart(alt_records(df)).encode(
        x=alt.X("event_ts:T", title=None, axis=alt.Axis(format="%H:%M", labelAngle=0)),
        tooltip=[
            alt.Tooltip("event_ts:T", title="timestamp", format="%H:%M:%S"),
            alt.Tooltip("ingestion_latency_ms:Q", title="latencia ms", format=".2f"),
            alt.Tooltip("estado:N", title="estado"),
        ],
    )
    chart = alt.layer(
        base.mark_area(color=COLOR_STEEL, opacity=0.13).encode(y=alt.Y("ingestion_latency_ms:Q", title="ms", scale=alt.Scale(zero=False, padding=8))),
        base.mark_line(color=COLOR_STEEL, strokeWidth=2.8).encode(y=alt.Y("ingestion_latency_ms:Q", title="ms", scale=alt.Scale(zero=False, padding=8))),
        base.mark_circle(size=55, color=COLOR_STEEL, opacity=0.88).encode(y=alt.Y("ingestion_latency_ms:Q", title="ms", scale=alt.Scale(zero=False, padding=8))),
    ).properties(height=280, title="Latencia de ingesta")
    st.altair_chart(style_chart(chart), use_container_width=True)


def render_gold_risk_strip(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("Sin ventanas Oro para graficar.")
        return

    chart = (
        alt.Chart(alt_records(df))
        .mark_rect()
        .encode(
            x=alt.X("event_minute:T", title=None, axis=alt.Axis(format="%H:%M", labelAngle=0)),
            y=alt.Y("equipment_id:N", title=None),
            color=alt.Color(
                "dominant_risk_level:N",
                title="riesgo",
                scale=alt.Scale(domain=RISK_COLOR_DOMAIN, range=RISK_COLOR_RANGE),
            ),
            tooltip=[
                alt.Tooltip("event_minute:T", title="minuto", format="%Y-%m-%d %H:%M"),
                alt.Tooltip("equipment_id:N", title="equipo"),
                alt.Tooltip("riesgo:N", title="riesgo"),
                alt.Tooltip("event_count:Q", title="eventos"),
                alt.Tooltip("critical_events:Q", title="criticos"),
            ],
        )
        .properties(height=170, title="Cinta de riesgo historico")
    )
    st.altair_chart(style_chart(chart), use_container_width=True)


def render_gold_temperature_chart(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("Sin temperaturas Oro para graficar.")
        return

    folded = df.melt(
        id_vars=["event_minute", "dominant_risk_level", "riesgo"],
        value_vars=["avg_temperature_c", "max_temperature_c"],
        var_name="serie",
        value_name="temperatura_c",
    )
    folded["serie"] = folded["serie"].map(
        {
            "avg_temperature_c": "promedio",
            "max_temperature_c": "maxima",
        }
    )
    base = alt.Chart(alt_records(folded)).encode(
        x=alt.X("event_minute:T", title=None, axis=alt.Axis(format="%H:%M", labelAngle=0)),
        y=alt.Y("temperatura_c:Q", title="C", scale=alt.Scale(zero=False)),
        color=alt.Color("serie:N", title="temperatura", scale=alt.Scale(range=[COLOR_STEEL, COLOR_AMBER])),
        tooltip=[
            alt.Tooltip("event_minute:T", title="minuto", format="%H:%M"),
            alt.Tooltip("serie:N", title="serie"),
            alt.Tooltip("temperatura_c:Q", title="temp C", format=".2f"),
            alt.Tooltip("riesgo:N", title="riesgo"),
        ],
    )
    rules = alt.Chart(
        alt_values([
            {"limite": TEMP_WARNING_C, "tipo": "advertencia"},
            {"limite": TEMP_CRITICAL_C, "tipo": "critico"},
        ])
    ).mark_rule(strokeDash=[5, 4], strokeWidth=1.2).encode(
        y="limite:Q",
        color=alt.Color(
            "tipo:N",
            title="umbral",
            scale=alt.Scale(domain=["advertencia", "critico"], range=[COLOR_AMBER, COLOR_RED]),
        ),
    )
    chart = alt.layer(base.mark_line(strokeWidth=2.8), base.mark_circle(size=55), rules).properties(
        height=300, title="Temperatura Oro"
    )
    st.altair_chart(style_chart(chart), use_container_width=True)


def render_gold_pressure_chart(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("Sin presion Oro para graficar.")
        return

    base = alt.Chart(alt_records(df)).encode(
        x=alt.X("event_minute:T", title=None, axis=alt.Axis(format="%H:%M", labelAngle=0)),
        y=alt.Y("min_lubrication_pressure_bar:Q", title="bar", scale=alt.Scale(zero=False)),
        tooltip=[
            alt.Tooltip("event_minute:T", title="minuto", format="%H:%M"),
            alt.Tooltip("min_lubrication_pressure_bar:Q", title="presion minima", format=".2f"),
            alt.Tooltip("riesgo:N", title="riesgo"),
        ],
    )
    rules = alt.Chart(
        alt_values([
            {"limite": PRESSURE_WARNING_BAR, "tipo": "advertencia"},
            {"limite": PRESSURE_CRITICAL_BAR, "tipo": "critico"},
        ])
    ).mark_rule(strokeDash=[5, 4], strokeWidth=1.2).encode(
        y="limite:Q",
        color=alt.Color(
            "tipo:N",
            title="umbral",
            scale=alt.Scale(domain=["advertencia", "critico"], range=[COLOR_AMBER, COLOR_RED]),
        ),
    )
    chart = alt.layer(
        base.mark_area(color=COLOR_GREEN, opacity=0.14),
        base.mark_line(color=COLOR_GREEN, strokeWidth=2.8),
        base.mark_circle(color=COLOR_GREEN, size=55),
        rules,
    ).properties(height=300, title="Presion minima de lubricacion")
    st.altair_chart(style_chart(chart), use_container_width=True)


def render_gold_event_stack(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("Sin eventos Oro para graficar.")
        return

    folded = df.melt(
        id_vars=["event_minute"],
        value_vars=["anomaly_events", "warning_events", "critical_events"],
        var_name="tipo",
        value_name="eventos",
    )
    folded["tipo"] = folded["tipo"].map(
        {
            "anomaly_events": "anomalias",
            "warning_events": "advertencias",
            "critical_events": "criticos",
        }
    )
    chart = (
        alt.Chart(alt_records(folded))
        .mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2)
        .encode(
            x=alt.X("event_minute:T", title=None, axis=alt.Axis(format="%H:%M", labelAngle=0)),
            y=alt.Y("eventos:Q", title="eventos"),
            color=alt.Color(
                "tipo:N",
                title="tipo",
                scale=alt.Scale(domain=["anomalias", "advertencias", "criticos"], range=[COLOR_PURPLE, COLOR_AMBER, COLOR_RED]),
            ),
            tooltip=[
                alt.Tooltip("event_minute:T", title="minuto", format="%H:%M"),
                alt.Tooltip("tipo:N", title="tipo"),
                alt.Tooltip("eventos:Q", title="eventos"),
            ],
        )
        .properties(height=300, title="Eventos de riesgo por minuto")
    )
    st.altair_chart(style_chart(chart), use_container_width=True)


def metric_card(label: str, value: str, foot: str, tone: str = "") -> str:
    tone_class = f" {tone}" if tone else ""
    return (
        f'<div class="kpi-card{tone_class}">'
        f'<div class="kpi-label">{esc(label)}</div>'
        f'<div class="kpi-value">{esc(value)}</div>'
        f'<div class="kpi-foot">{esc(foot)}</div>'
        "</div>"
    )


def render_kpi_grid(cards: list[str]) -> None:
    st.html(f'<div class="kpi-grid">{"".join(cards)}</div>')


st.set_page_config(
    page_title="Control Operacional Minero",
    page_icon="M",
    layout="wide",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Instrument+Sans:wght@400;500;600&display=swap');

    :root {
        --bg: #f5f7f8;
        --panel: rgba(255, 255, 255, 0.92);
        --panel-strong: #ffffff;
        --text: #1d2733;
        --muted: #667085;
        --line: rgba(16, 24, 40, 0.12);
        --green: #16724f;
        --amber: #b86b14;
        --danger: #b42318;
        --steel: #36556d;
        --blue: #2563eb;
    }

    .stApp {
        font-family: "Instrument Sans", sans-serif;
        color: var(--text);
        background: linear-gradient(180deg, #f6f8f9 0%, #edf1f3 100%);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(20, 36, 48, 0.98) 0%, rgba(22, 67, 59, 0.98) 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    [data-testid="stSidebar"] * {
        color: #f2f7f5 !important;
        font-family: "Instrument Sans", sans-serif !important;
    }

    [data-testid="stSidebar"] .stButton button {
        background: #f8fafc !important;
        border: 1px solid rgba(255, 255, 255, 0.45) !important;
        color: #12313a !important;
        font-weight: 700 !important;
    }

    [data-testid="stSidebar"] .stButton button * {
        color: #12313a !important;
    }

    [data-testid="stSidebar"] .stButton button:hover {
        background: #ffffff !important;
        border-color: #ff5a66 !important;
        color: #0f2430 !important;
    }

    .block-container {
        padding-top: 1.25rem;
        padding-bottom: 2.2rem;
        max-width: 1520px;
    }

    h1, h2, h3 {
        font-family: "Space Grotesk", sans-serif !important;
        letter-spacing: 0;
    }

    div[data-testid="stMetric"] {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 0.85rem 0.9rem;
    }

    .topband {
        display: grid;
        grid-template-columns: 1.75fr 1fr;
        gap: 1rem;
        margin-bottom: 1rem;
    }

    .hero {
        background: linear-gradient(135deg, rgba(20, 36, 48, 0.98) 0%, rgba(22, 88, 74, 0.94) 100%);
        color: #f6fff7;
        border-radius: 8px;
        padding: 1.4rem 1.5rem;
        box-shadow: 0 18px 44px rgba(20, 36, 48, 0.15);
        min-height: 222px;
    }

    .hero-kicker {
        text-transform: uppercase;
        font-size: 0.76rem;
        letter-spacing: 0.14em;
        opacity: 0.72;
    }

    .hero-title {
        font-family: "Space Grotesk", sans-serif;
        font-size: 2.35rem;
        line-height: 1;
        margin-top: 0.55rem;
        font-weight: 700;
    }

    .hero-sub {
        margin-top: 0.75rem;
        max-width: 64ch;
        opacity: 0.86;
        font-size: 0.99rem;
    }

    .hero-meta {
        display: flex;
        gap: 0.7rem;
        flex-wrap: wrap;
        margin-top: 1rem;
    }

    .hero-pill {
        background: rgba(255, 255, 255, 0.09);
        border: 1px solid rgba(255, 255, 255, 0.10);
        border-radius: 8px;
        padding: 0.42rem 0.72rem;
        font-size: 0.88rem;
    }

    .signal-panel {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 1.2rem 1.25rem;
        box-shadow: 0 14px 34px rgba(80, 101, 94, 0.08);
        min-height: 222px;
    }

    .signal-label {
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-size: 0.75rem;
        color: var(--muted);
    }

    .signal-value {
        font-family: "Space Grotesk", sans-serif;
        font-size: 2.05rem;
        margin-top: 0.3rem;
        font-weight: 700;
    }

    .signal-copy {
        margin-top: 0.45rem;
        color: var(--muted);
        font-size: 0.96rem;
    }

    .section-heading {
        margin-top: 0.6rem;
        margin-bottom: 0.55rem;
    }

    .decision-note {
        background: rgba(255, 255, 255, 0.85);
        border-left: 4px solid var(--steel);
        border-radius: 0 8px 8px 0;
        color: #344054;
        padding: 0.75rem 0.95rem;
        margin: 0.4rem 0 1rem;
        font-size: 0.93rem;
        line-height: 1.5;
    }

    /* chart container */
    div[data-testid="stVegaLiteChart"] {
        border-radius: 10px;
        overflow: hidden;
        background: var(--panel-strong);
        border: 1px solid var(--line);
        padding: 0.5rem 0.25rem 0.25rem;
        box-shadow: 0 1px 4px rgba(16, 24, 40, 0.05);
    }

    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.85rem;
        margin: 0.85rem 0 1rem;
    }

    .kpi-card {
        background: var(--panel-strong);
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 1.1rem 1.15rem;
        min-height: 130px;
        box-shadow: 0 2px 8px rgba(16, 24, 40, 0.06), 0 1px 2px rgba(16, 24, 40, 0.04);
        transition: box-shadow 0.2s;
    }

    .kpi-card:hover {
        box-shadow: 0 8px 24px rgba(16, 24, 40, 0.10);
    }

    .kpi-card.danger {
        border-left: 5px solid var(--danger);
        background: linear-gradient(135deg, #fff 0%, rgba(180, 35, 24, 0.03) 100%);
    }

    .kpi-card.warning {
        border-left: 5px solid var(--amber);
        background: linear-gradient(135deg, #fff 0%, rgba(184, 107, 20, 0.03) 100%);
    }

    .kpi-card.ok {
        border-left: 5px solid var(--green);
        background: linear-gradient(135deg, #fff 0%, rgba(22, 114, 79, 0.03) 100%);
    }

    .kpi-label {
        font-size: 0.76rem;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.10em;
        font-weight: 600;
    }

    .kpi-value {
        font-family: "Space Grotesk", sans-serif;
        font-size: 2rem;
        font-weight: 700;
        margin-top: 0.5rem;
        line-height: 1;
        color: var(--text);
    }

    .kpi-card.danger .kpi-value { color: var(--danger); }
    .kpi-card.warning .kpi-value { color: var(--amber); }
    .kpi-card.ok .kpi-value { color: #166534; }

    .kpi-foot {
        margin-top: 0.65rem;
        font-size: 0.85rem;
        color: var(--muted);
        line-height: 1.4;
    }

    .insight-box {
        background: var(--panel-strong);
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 1.1rem 1.15rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 2px 8px rgba(16, 24, 40, 0.05);
        line-height: 1.6;
    }

    .alert-card {
        border-radius: 10px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.8rem;
        background: var(--panel-strong);
        border: 1px solid var(--line);
        box-shadow: 0 2px 8px rgba(60, 70, 80, 0.06);
    }

    .alert-title {
        font-family: "Space Grotesk", sans-serif;
        font-size: 1.04rem;
        font-weight: 700;
        letter-spacing: -0.01em;
    }

    .mini-chip {
        display: inline-block;
        padding: 0.22rem 0.5rem;
        border-radius: 6px;
        font-size: 0.8rem;
        margin-right: 0.35rem;
        margin-top: 0.35rem;
        background: rgba(52, 64, 84, 0.08);
        color: #344054;
    }

    .status-running {
        background: rgba(22, 114, 79, 0.12);
        color: #166534;
    }

    .status-warning {
        background: rgba(184, 107, 20, 0.14);
        color: #92400e;
    }

    .status-critical {
        background: rgba(180, 35, 24, 0.14);
        color: #991b1b;
    }

    .subtle-note {
        color: var(--muted);
        font-size: 0.92rem;
    }

    div[data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid var(--line);
        background: rgba(255, 255, 255, 0.86);
    }

    .layer-strip {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.85rem;
        margin: 0.85rem 0 1.1rem;
    }

    .layer-step {
        background: var(--panel-strong);
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 1rem 1.05rem;
        box-shadow: 0 1px 4px rgba(16, 24, 40, 0.05);
        position: relative;
        overflow: hidden;
    }

    .layer-step::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--steel) 0%, var(--blue) 100%);
        border-radius: 10px 10px 0 0;
    }

    .layer-name {
        font-family: "Space Grotesk", sans-serif;
        font-size: 1rem;
        font-weight: 700;
        color: var(--text);
        margin-top: 0.35rem;
    }

    .layer-copy {
        color: var(--muted);
        font-size: 0.88rem;
        margin-top: 0.3rem;
        line-height: 1.45;
    }

    @media (max-width: 1100px) {
        .topband, .kpi-grid, .layer-strip {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Control Operacional Minero")
st.caption("Telemetria de molino SAG, alertas y salud del pipeline de datos.")

with st.sidebar:
    st.header("Parametros")
    metrics_window = st.slider("Ventana operacional", min_value=10, max_value=200, value=50, step=10)
    trend_window = st.slider("Tendencia reciente", min_value=20, max_value=200, value=80, step=10)
    recent_limit = st.slider("Lecturas en tabla", min_value=5, max_value=30, value=10, step=5)
    alert_limit = st.slider("Alertas visibles", min_value=5, max_value=30, value=10, step=5)
    st.divider()
    auto_refresh = st.checkbox("Auto-actualizar", value=True)
    refresh_interval = st.select_slider(
        "Intervalo (segundos)",
        options=[15, 30, 60, 120],
        value=30,
        disabled=not auto_refresh,
    )
    st.caption("Ajusta la ventana de analisis y refresca la vista.")
    if st.button("Actualizar ahora", use_container_width=True):
        st.rerun()


health = fetch_json("/health", default={"status": None, "service": "api"})
metrics_payload = fetch_json(
    "/api/v1/metrics/summary",
    params={"window": metrics_window},
    default={"window": metrics_window, "metrics": {}},
)
pipeline_payload = fetch_json("/api/v1/pipeline/metrics", default={"metrics": {}})
alerts_payload = fetch_json("/api/v1/alerts/active", params={"limit": alert_limit}, default={"count": 0, "items": []})
recent_payload = fetch_json(
    "/api/v1/telemetry/recent", params={"limit": recent_limit}, default={"count": 0, "items": []}
)
trends_payload = fetch_json(
    "/api/v1/telemetry/trends", params={"window": trend_window}, default={"count": 0, "items": []}
)
gold_rows = load_gold_summary(GOLD_SUMMARY_PATH)
gold_report = load_gold_report(GOLD_REPORT_PATH)

metrics = metrics_payload.get("metrics", {})
pipeline_metrics = pipeline_payload.get("metrics", {})
alerts = alerts_payload.get("items", [])
trends = trends_payload.get("items", [])
recent_items = recent_payload.get("items", [])
gold_summary = summarize_gold(gold_rows)
trends_df = build_trends_df(trends)
alerts_df = build_alerts_df(alerts)
recent_table_rows = build_recent_rows(recent_items)
gold_df = build_gold_df(gold_rows)
latest_gold_df = gold_df.tail(48)
latest_gold_rows = gold_rows[-min(len(gold_rows), 8) :]
api_online = health.get("status") == "ok" and not API_ERRORS
risk_label, risk_color, risk_copy = risk_badge(metrics, alerts, api_online)
latest_critical = latest_critical_alert(alerts)

if API_ERRORS:
    st.warning(
        f"Tiempo real sin conexion completa con la API en {API_BASE_URL}. "
        "La capa historica Oro sigue disponible desde archivos locales."
    )
    with st.expander("Detalle tecnico de conexion"):
        for error in API_ERRORS[:6]:
            st.code(error)

st.markdown(
    f"""
    <div class="topband">
        <div class="hero">
            <div class="hero-kicker">Consola operacional en tiempo real</div>
            <div class="hero-title">Pulso del Molino SAG</div>
            <div class="hero-sub">
                Lectura rapida de estado, riesgo y confiabilidad del dato. Cada senal muestra si el
                molino opera normal, que variable se desvia y si el pipeline esta entregando informacion util.
            </div>
            <div class="hero-meta">
                <div class="hero-pill">API: {esc(translate_service_status(health.get('status')))}</div>
                <div class="hero-pill">Ultimo evento: {esc(fmt_timestamp(metrics.get('latest_event_ts')))}</div>
                <div class="hero-pill">Eventos raw: {esc(fmt_compact(metrics.get('total_events', 0), 0))}</div>
                <div class="hero-pill">Ventanas Oro: {esc(fmt_compact(gold_summary.get('window_count', 0), 0))}</div>
            </div>
        </div>
        <div class="signal-panel">
            <div class="signal-label">Decision operacional ahora</div>
            <div class="signal-value" style="color:{risk_color};">{esc(risk_label)}</div>
            <div class="signal-copy">{esc(risk_copy)}</div>
            <div style="margin-top:1rem;border-top:1px solid var(--line);padding-top:0.9rem;">
                <div class="subtle-note">Advertencias: {esc(to_int(metrics.get('warning_events', 0)))}</div>
                <div class="subtle-note">Criticos: {esc(to_int(metrics.get('critical_events', 0)))}</div>
                <div class="subtle-note">Latencia promedio: {esc(fmt_number(metrics.get('avg_ingestion_latency_ms'), 2))} ms</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="layer-strip">
        <div class="layer-step">
            <div class="layer-name">Bronce</div>
            <div class="layer-copy">{esc(fmt_compact(metrics.get('total_events', 0), 0))} eventos crudos persistidos para trazabilidad.</div>
        </div>
        <div class="layer-step">
            <div class="layer-name">Plata</div>
            <div class="layer-copy">{esc(fmt_compact(gold_report.get('input_rows', 0), 0))} filas limpias preparadas para analitica.</div>
        </div>
        <div class="layer-step">
            <div class="layer-name">Oro</div>
            <div class="layer-copy">{esc(fmt_compact(gold_summary.get('window_count', 0), 0))} ventanas por minuto para lectura ejecutiva.</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

event_tone = "ok" if risk_label == "Estable" else "warning" if risk_label == "Advertencia" else "danger"
render_kpi_grid(
    [
        metric_card(
            "Eventos en ventana",
            fmt_compact(metrics.get("window_events", 0), 0),
            f"Ultimo estado: {translate_state(metrics.get('latest_operational_state'))}",
            event_tone,
        ),
        metric_card(
            "Temperatura",
            f"{fmt_number(metrics.get('avg_temperature_c'), 2)} C",
            f"Maxima: {fmt_number(metrics.get('max_temperature_c'), 2)} C | critico >= {TEMP_CRITICAL_C:.0f} C",
            "danger" if to_float(metrics.get("max_temperature_c")) >= TEMP_CRITICAL_C else "warning"
            if to_float(metrics.get("max_temperature_c")) >= TEMP_WARNING_C
            else "ok",
        ),
        metric_card(
            "Vibracion",
            f"{fmt_number(metrics.get('avg_vibration_mm_s'), 2)} mm/s",
            f"Umbral de alerta: {VIBRATION_WARNING_MM_S:.1f} mm/s",
            "warning" if to_float(metrics.get("avg_vibration_mm_s")) >= VIBRATION_WARNING_MM_S else "ok",
        ),
        metric_card(
            "Anomalia",
            fmt_number(metrics.get("avg_anomaly_score"), 3),
            f"Alerta desde {ANOMALY_WARNING_SCORE:.1f}; calidad no OK: {to_int(metrics.get('non_ok_quality_events', 0))}",
            "warning" if to_float(metrics.get("avg_anomaly_score")) >= 0.65 else "ok",
        ),
    ]
)

tab_control, tab_alerts, tab_telemetry, tab_pipeline, tab_historical = st.tabs(
    ["Control", "Riesgo y Alertas", "Telemetria", "Pipeline", "Historico Oro"]
)

with tab_control:
    st.markdown('<div class="section-heading">', unsafe_allow_html=True)
    st.subheader("Lectura operacional")
    st.markdown(
        '<div class="decision-note">La vista principal separa las senales por unidad para no mezclar escalas: '
        "temperatura, vibracion, lubricacion y anomalia muestran sus propios umbrales.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        render_metric_chart(
            trends_df,
            "temperature_c",
            "Temperatura",
            "°C",
            COLOR_AMBER,
            warning=TEMP_WARNING_C,
            critical=TEMP_CRITICAL_C,
            y_domain=(58.0, 92.0),
        )
    with c2:
        render_metric_chart(
            trends_df,
            "vibration_mm_s",
            "Vibracion",
            "mm/s",
            COLOR_BLUE,
            warning=VIBRATION_WARNING_MM_S,
            critical=VIBRATION_CRITICAL_MM_S,
            y_domain=(0.0, 6.5),
        )

    c3, c4 = st.columns(2)
    with c3:
        render_metric_chart(
            trends_df,
            "lubrication_pressure_bar",
            "Presion de lubricacion",
            "bar",
            COLOR_GREEN,
            warning=PRESSURE_WARNING_BAR,
            critical=PRESSURE_CRITICAL_BAR,
            y_domain=(1.2, 5.2),
        )
    with c4:
        render_anomaly_chart(trends_df)

    c5, c6 = st.columns([1.45, 1])
    with c5:
        render_state_timeline(trends_df)
    with c6:
        st.markdown(
            f"""
            <div class="insight-box">
                <strong>Lectura rapida</strong><br>
                Riesgo actual: <span style="color:{risk_color};font-weight:700;">{esc(risk_label)}</span><br>
                Ventana analizada: {esc(metrics_payload.get('window', metrics_window))} eventos<br>
                Calidad no OK: {esc(fmt_compact(metrics.get('non_ok_quality_events', 0), 0))}<br>
                Presion promedio: {esc(fmt_number(metrics.get('avg_lubrication_pressure_bar'), 2))} bar
            </div>
            """,
            unsafe_allow_html=True,
        )
        if latest_critical:
            st.markdown(
                f"""
                <div class="insight-box">
                    <strong>Ultima critica</strong><br>
                    {esc(translate_alert_reason(latest_critical.get('alert_reason')))}<br>
                    Temp: {esc(fmt_number(latest_critical.get('temperature_c'), 2))} C<br>
                    Vib: {esc(fmt_number(latest_critical.get('vibration_mm_s'), 2))} mm/s<br>
                    Presion: {esc(fmt_number(latest_critical.get('lubrication_pressure_bar'), 2))} bar
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="insight-box">
                    <strong>Ultima critica</strong><br>
                    No hay alerta critica activa en la ventana inspeccionada.
                </div>
                """,
                unsafe_allow_html=True,
            )

with tab_alerts:
    st.subheader("Riesgo y alertas")
    st.markdown(
        '<div class="decision-note">Esta vista explica por que existe riesgo: severidad, motivo y variable operacional afectada.</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 1.15])
    with left:
        render_alert_reason_chart(alerts_df)
    with right:
        render_state_distribution(trends_df)

    if not alerts:
        st.info("No hay alertas activas en la ventana inspeccionada.")
    else:
        for alert in alerts:
            severity = alert.get("alert_severity", "warning")
            color = severity_color(severity)
            status_class = status_variant(alert.get("operational_state", "running"))
            st.markdown(
                f"""
                <div class="alert-card" style="border-left: 8px solid {color};">
                    <div class="alert-title" style="color:{color};">{esc(translate_state(severity).upper())} · {esc(translate_alert_reason(alert.get('alert_reason')))}</div>
                    <div class="subtle-note" style="margin-top:0.35rem;">
                        Equipo {esc(alert.get('equipment_id', 'n/a'))} en {esc(alert.get('site', 'n/a'))} / {esc(alert.get('line', 'n/a'))}<br>
                        Timestamp: {esc(fmt_timestamp(alert.get('event_ts')))}
                    </div>
                    <div style="margin-top:0.5rem;">
                        <span class="mini-chip {status_class}">estado: {esc(translate_state(alert.get('operational_state')))}</span>
                        <span class="mini-chip">temp: {esc(fmt_number(alert.get('temperature_c'), 2))} C</span>
                        <span class="mini-chip">vibracion: {esc(fmt_number(alert.get('vibration_mm_s'), 2))} mm/s</span>
                        <span class="mini-chip">presion: {esc(fmt_number(alert.get('lubrication_pressure_bar'), 2))} bar</span>
                        <span class="mini-chip">anomalia: {esc(fmt_number(alert.get('anomaly_score'), 3))}</span>
                        <span class="mini-chip">calidad: {esc(translate_quality_flag(alert.get('quality_flag')))}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

with tab_telemetry:
    st.subheader("Telemetria reciente")
    st.markdown(
        '<div class="decision-note">Tabla compacta para auditar las ultimas lecturas: evento, estado, variables criticas, calidad y latencia.</div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Lecturas visibles", len(recent_table_rows))
    with c2:
        st.metric("Eventos/min", fmt_compact(pipeline_metrics.get("events_ingested_per_minute", 0), 0))
    with c3:
        st.metric("Latencia prom.", f"{fmt_number(pipeline_metrics.get('event_ingestion_latency_ms'), 2)} ms")

    if recent_table_rows:
        st.dataframe(recent_table_rows, use_container_width=True, hide_index=True)
    else:
        st.info("Sin telemetria reciente. Levanta el stack local para recibir lecturas vivas.")

with tab_pipeline:
    st.subheader("Confiabilidad del pipeline")
    st.markdown(
        '<div class="decision-note">El pipeline tambien se monitorea: no basta con ver el molino, hay que confiar en que los datos llegaron completos y a tiempo.</div>',
        unsafe_allow_html=True,
    )

    render_kpi_grid(
        [
            metric_card(
                "Aceptados",
                fmt_compact(pipeline_metrics.get("accepted_events", 0), 0),
                "Mensajes persistidos en raw.",
                "ok",
            ),
            metric_card(
                "Rechazados",
                fmt_compact(pipeline_metrics.get("invalid_events_dead_lettered", 0), 0),
                "Mensajes enviados a dead-letter.",
                "danger" if to_int(pipeline_metrics.get("invalid_events_dead_lettered", 0)) > 0 else "ok",
            ),
            metric_card(
                "Tasa de error",
                f"{fmt_number(to_float(pipeline_metrics.get('ingestion_error_rate', 0)) * 100, 2)}%",
                "Rechazados sobre total observado.",
                "warning" if to_float(pipeline_metrics.get("ingestion_error_rate", 0)) > 0 else "ok",
            ),
            metric_card(
                "Eventos/min",
                fmt_compact(pipeline_metrics.get("events_ingested_per_minute", 0), 0),
                "Mensajes aceptados en el ultimo minuto.",
                "ok",
            ),
        ]
    )

    left, right = st.columns(2)
    with left:
        render_pipeline_quality_chart(pipeline_metrics)
    with right:
        render_latency_chart(trends_df)

    left, right = st.columns(2)
    with left:
        st.markdown(
            f"""
            <div class="insight-box">
                <strong>Latencia</strong><br>
                Promedio: {esc(fmt_number(pipeline_metrics.get('event_ingestion_latency_ms'), 2))} ms<br>
                Maxima: {esc(fmt_number(pipeline_metrics.get('max_ingestion_latency_ms'), 2))} ms
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f"""
            <div class="insight-box">
                <strong>Ultima actividad</strong><br>
                Ultimo aceptado: {esc(fmt_timestamp(pipeline_metrics.get('latest_accepted_at')))}<br>
                Ultimo rechazado: {esc(fmt_timestamp(pipeline_metrics.get('latest_rejected_at')))}
            </div>
            """,
            unsafe_allow_html=True,
        )

with tab_historical:
    st.subheader("Historico Oro")
    st.markdown(
        '<div class="decision-note">Oro resume la operacion por minuto: menos filas, mas contexto para revisar riesgo historico y resultados de la demo.</div>',
        unsafe_allow_html=True,
    )
    if gold_df.empty:
        st.info("Aun no existe el resumen Oro. El servicio processor lo genera automaticamente cada 60 segundos.")
    else:
        render_kpi_grid(
            [
                metric_card(
                    "Ventanas Oro",
                    fmt_compact(gold_summary.get("window_count"), 0),
                    "Resumenes por minuto y equipo.",
                    "ok",
                ),
                metric_card(
                    "Criticos",
                    fmt_compact(gold_summary.get("critical_events"), 0),
                    "Eventos criticos agregados.",
                    "danger" if to_int(gold_summary.get("critical_events", 0)) > 0 else "ok",
                ),
                metric_card(
                    "Anomalias",
                    fmt_compact(gold_summary.get("anomaly_events"), 0),
                    "Lecturas anomalas despues de Plata.",
                    "warning" if to_int(gold_summary.get("anomaly_events", 0)) > 0 else "ok",
                ),
                metric_card(
                    "Riesgo dominante",
                    translate_risk(gold_summary.get("dominant_risk_level", "n/a")),
                    "Mayor riesgo observado.",
                    "danger" if gold_summary.get("dominant_risk_level") == "critical" else "warning"
                    if gold_summary.get("dominant_risk_level") == "warning"
                    else "ok",
                ),
            ]
        )

        render_gold_risk_strip(latest_gold_df)

        left, right = st.columns(2)
        with left:
            render_gold_temperature_chart(latest_gold_df)
        with right:
            render_gold_pressure_chart(latest_gold_df)

        left, right = st.columns([1.25, 1])
        with left:
            render_gold_event_stack(latest_gold_df)
        with right:
            st.markdown(
                f"""
                <div class="insight-box">
                    <strong>Perfil historico</strong><br>
                    Eventos resumidos: {esc(fmt_compact(gold_summary.get('event_count'), 0))}<br>
                    Temp. promedio: {esc(fmt_number(gold_summary.get('avg_temperature_c'), 2))} C<br>
                    Temp. maxima: {esc(fmt_number(gold_summary.get('max_temperature_c'), 2))} C<br>
                    Vibracion promedio: {esc(fmt_number(gold_summary.get('avg_vibration_mm_s'), 2))} mm/s<br>
                    Presion minima: {esc(fmt_number(gold_summary.get('min_lubrication_pressure_bar'), 2))} bar
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
                <div class="insight-box">
                    <strong>Calidad de transformacion</strong><br>
                    Latencia promedio: {esc(fmt_number(gold_summary.get('avg_latency_ms'), 2))} ms<br>
                    Filas malformadas omitidas: {esc(fmt_compact(gold_report.get('malformed_rows_skipped', 0), 0))}<br>
                    Filas Oro generadas: {esc(fmt_compact(gold_report.get('output_rows', 0), 0))}
                </div>
                """,
                unsafe_allow_html=True,
            )

        latest_rows = [
            {
                "minuto": fmt_timestamp(row["event_minute"]),
                "eventos": row["event_count"],
                "temp_max_c": row["max_temperature_c"],
                "presion_min_bar": row["min_lubrication_pressure_bar"],
                "anomalias": row["anomaly_events"],
                "advertencias": row["warning_events"],
                "criticos": row["critical_events"],
                "riesgo": translate_risk(row["dominant_risk_level"]),
            }
            for row in latest_gold_rows
        ]
        st.dataframe(latest_rows, use_container_width=True, hide_index=True)

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
