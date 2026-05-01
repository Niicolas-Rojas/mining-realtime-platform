import json
from datetime import UTC, datetime
from pathlib import Path
import sys
import uuid


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SERVICE_ROOT = PROJECT_ROOT / "ingestion"
for module_name in list(sys.modules):
    if module_name == "src" or module_name.startswith("src."):
        del sys.modules[module_name]
sys.path.insert(0, str(SERVICE_ROOT))

from src import main as ingestion_main
from src.config import IngestionConfig
from src.main import process_message_payload


def valid_event() -> dict:
    return {
        "event_id": str(uuid.uuid4()),
        "event_ts": datetime.now(UTC).isoformat(),
        "equipment_id": "sag-mill-01",
        "site": "concentradora-norte",
        "line": "linea-a",
        "operational_state": "running",
        "temperature_c": 70.1,
        "vibration_mm_s": 2.8,
        "lubrication_pressure_bar": 3.4,
        "rpm": 9.6,
        "amperage_a": 420.0,
        "power_kw": 5010.0,
        "flow_m3_h": 118.4,
        "anomaly_score": 0.12,
        "quality_flag": "ok",
    }


def test_process_message_payload_persists_valid_payload(monkeypatch) -> None:
    persisted_payloads = []
    bronze_payloads = []
    rejected_payloads = []
    dead_letters = []

    monkeypatch.setattr(
        ingestion_main,
        "persist_event",
        lambda _connection, payload: persisted_payloads.append(payload),
    )
    monkeypatch.setattr(
        ingestion_main,
        "write_bronze_record",
        lambda _output_path, payload: bronze_payloads.append(payload),
    )
    monkeypatch.setattr(
        ingestion_main,
        "persist_rejected_event",
        lambda *_args, **kwargs: rejected_payloads.append(kwargs),
    )
    monkeypatch.setattr(
        ingestion_main,
        "write_dead_letter_record",
        lambda *_args, **kwargs: dead_letters.append(kwargs),
    )

    accepted = process_message_payload(
        raw_payload=json.dumps(valid_event()).encode("utf-8"),
        config=IngestionConfig(),
        connection=object(),
        topic="mining/sag-mill/telemetry",
    )

    assert accepted is True
    assert len(persisted_payloads) == 1
    assert len(bronze_payloads) == 1
    assert rejected_payloads == []
    assert dead_letters == []


def test_process_message_payload_dead_letters_invalid_payload(monkeypatch) -> None:
    persisted_payloads = []
    bronze_payloads = []
    rejected_payloads = []
    dead_letters = []

    monkeypatch.setattr(
        ingestion_main,
        "persist_event",
        lambda _connection, payload: persisted_payloads.append(payload),
    )
    monkeypatch.setattr(
        ingestion_main,
        "write_bronze_record",
        lambda _output_path, payload: bronze_payloads.append(payload),
    )
    monkeypatch.setattr(
        ingestion_main,
        "persist_rejected_event",
        lambda *_args, **kwargs: rejected_payloads.append(kwargs),
    )
    monkeypatch.setattr(
        ingestion_main,
        "write_dead_letter_record",
        lambda *_args, **kwargs: dead_letters.append(kwargs),
    )

    invalid_event = valid_event()
    invalid_event["temperature_c"] = "too-hot"

    accepted = process_message_payload(
        raw_payload=json.dumps(invalid_event).encode("utf-8"),
        config=IngestionConfig(),
        connection=object(),
        topic="mining/sag-mill/telemetry",
    )

    assert accepted is False
    assert persisted_payloads == []
    assert bronze_payloads == []
    assert rejected_payloads[0]["reason"].startswith("schema_validation_failed")
    assert dead_letters[0]["reason"].startswith("schema_validation_failed")


def test_process_message_payload_dead_letters_invalid_json(monkeypatch) -> None:
    rejected_payloads = []
    dead_letters = []

    monkeypatch.setattr(
        ingestion_main,
        "persist_rejected_event",
        lambda *_args, **kwargs: rejected_payloads.append(kwargs),
    )
    monkeypatch.setattr(
        ingestion_main,
        "write_dead_letter_record",
        lambda *_args, **kwargs: dead_letters.append(kwargs),
    )

    accepted = process_message_payload(
        raw_payload=b"{not-json",
        config=IngestionConfig(),
        connection=object(),
        topic="mining/sag-mill/telemetry",
    )

    assert accepted is False
    assert rejected_payloads[0]["reason"].startswith("invalid_json")
    assert dead_letters[0]["reason"].startswith("invalid_json")
