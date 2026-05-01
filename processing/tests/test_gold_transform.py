import csv
import json

from processing.batch.gold_transform import build_gold_dataset, summarize_group


def silver_row(
    event_minute: str = "2026-04-27T00:00:00+00:00",
    event_id: str = "evt-1",
    temperature_c: float = 70.0,
    risk_level: str = "normal",
    is_anomaly: bool = False,
    operational_state: str = "running",
) -> dict:
    return {
        "event_id": event_id,
        "event_ts": "2026-04-27T00:00:01+00:00",
        "event_date": "2026-04-27",
        "event_minute": event_minute,
        "ingested_at": "2026-04-27T00:00:02+00:00",
        "written_at": "2026-04-27T00:00:02+00:00",
        "ingestion_latency_ms": "1000.0",
        "equipment_id": "sag-mill-01",
        "site": "concentradora-norte",
        "line": "linea-a",
        "operational_state": operational_state,
        "temperature_c": str(temperature_c),
        "vibration_mm_s": "2.5",
        "lubrication_pressure_bar": "3.5",
        "rpm": "9.6",
        "amperage_a": "420.0",
        "power_kw": "5000.0",
        "flow_m3_h": "118.0",
        "anomaly_score": "0.8" if is_anomaly else "0.1",
        "quality_flag": "anomalous" if is_anomaly else "ok",
        "is_anomaly": str(is_anomaly),
        "is_quality_issue": str(is_anomaly),
        "is_flow_missing": "False",
        "risk_level": risk_level,
    }


def test_summarize_group_calculates_business_metrics() -> None:
    rows = [
        {
            "event_minute": "2026-04-27T00:00:00+00:00",
            "equipment_id": "sag-mill-01",
            "site": "concentradora-norte",
            "line": "linea-a",
            "operational_state": "running",
            "temperature_c": 70.0,
            "vibration_mm_s": 2.5,
            "lubrication_pressure_bar": 3.5,
            "power_kw": 5000.0,
            "anomaly_score": 0.1,
            "ingestion_latency_ms": 1000.0,
            "is_anomaly": False,
            "is_quality_issue": False,
            "is_flow_missing": False,
            "risk_level": "normal",
        },
        {
            "event_minute": "2026-04-27T00:00:00+00:00",
            "equipment_id": "sag-mill-01",
            "site": "concentradora-norte",
            "line": "linea-a",
            "operational_state": "warning",
            "temperature_c": 80.0,
            "vibration_mm_s": 5.0,
            "lubrication_pressure_bar": 2.7,
            "power_kw": 5200.0,
            "anomaly_score": 0.8,
            "ingestion_latency_ms": 2000.0,
            "is_anomaly": True,
            "is_quality_issue": True,
            "is_flow_missing": False,
            "risk_level": "warning",
        },
    ]

    summary = summarize_group(rows)

    assert summary["event_count"] == 2
    assert summary["avg_temperature_c"] == 75.0
    assert summary["max_vibration_mm_s"] == 5.0
    assert summary["min_lubrication_pressure_bar"] == 2.7
    assert summary["anomaly_events"] == 1
    assert summary["warning_events"] == 1
    assert summary["dominant_risk_level"] == "warning"


def test_build_gold_dataset_writes_minute_summary(tmp_path) -> None:
    input_path = tmp_path / "silver.csv"
    output_path = tmp_path / "gold.csv"
    report_path = tmp_path / "report.json"
    rows = [
        silver_row(event_id="evt-1", temperature_c=70.0),
        silver_row(event_id="evt-2", temperature_c=80.0, risk_level="warning", is_anomaly=True),
        silver_row(
            event_minute="2026-04-27T00:01:00+00:00",
            event_id="evt-3",
            temperature_c=72.0,
        ),
    ]

    with input_path.open("w", encoding="utf-8", newline="") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    result = build_gold_dataset(str(input_path), str(output_path), str(report_path))

    assert result.input_rows == 3
    assert result.output_rows == 2
    assert result.total_anomaly_events == 1

    with output_path.open("r", encoding="utf-8") as file_handle:
        summaries = list(csv.DictReader(file_handle))
    assert summaries[0]["event_count"] == "2"
    assert summaries[0]["avg_temperature_c"] == "75.0"
    assert summaries[0]["dominant_risk_level"] == "warning"

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["output_rows"] == 2
