import csv
import json

from processing.batch.silver_transform import build_silver_dataset, transform_bronze_record


def bronze_record(event_id: str = "evt-1") -> dict:
    return {
        "written_at": "2026-04-27T00:00:02+00:00",
        "payload": {
            "event_id": event_id,
            "event_ts": "2026-04-27T00:00:00+00:00",
            "equipment_id": "sag-mill-01",
            "site": "concentradora-norte",
            "line": "linea-a",
            "operational_state": "running",
            "temperature_c": 70.5,
            "vibration_mm_s": 2.4,
            "lubrication_pressure_bar": 3.5,
            "rpm": 9.6,
            "amperage_a": 420.0,
            "power_kw": 5010.0,
            "flow_m3_h": 118.4,
            "anomaly_score": 0.12,
            "quality_flag": "ok",
        },
    }


def test_transform_bronze_record_flattens_payload() -> None:
    row = transform_bronze_record(bronze_record())

    assert row["event_id"] == "evt-1"
    assert row["event_date"] == "2026-04-27"
    assert row["event_minute"] == "2026-04-27T00:00:00+00:00"
    assert row["ingestion_latency_ms"] == 2000.0
    assert row["risk_level"] == "normal"
    assert row["is_anomaly"] is False


def test_transform_bronze_record_marks_anomalies() -> None:
    record = bronze_record()
    record["payload"]["anomaly_score"] = 0.82
    record["payload"]["quality_flag"] = "anomalous"

    row = transform_bronze_record(record)

    assert row["is_anomaly"] is True
    assert row["is_quality_issue"] is True
    assert row["risk_level"] == "warning"


def test_build_silver_dataset_writes_csv_and_quality_report(tmp_path) -> None:
    input_path = tmp_path / "bronze.ndjson"
    output_path = tmp_path / "silver.csv"
    report_path = tmp_path / "quality.json"
    records = [
        bronze_record("evt-1"),
        bronze_record("evt-1"),
        {"broken": True},
        bronze_record("evt-2"),
    ]
    input_path.write_text(
        "\n".join(json.dumps(record) for record in records),
        encoding="utf-8",
    )

    result = build_silver_dataset(str(input_path), str(output_path), str(report_path))

    assert result.input_records == 4
    assert result.output_records == 2
    assert result.duplicate_events_skipped == 1
    assert result.malformed_records_skipped == 1

    with output_path.open("r", encoding="utf-8") as file_handle:
        rows = list(csv.DictReader(file_handle))
    assert [row["event_id"] for row in rows] == ["evt-1", "evt-2"]

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["output_records"] == 2
