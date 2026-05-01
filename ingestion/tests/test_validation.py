from datetime import UTC, datetime
from pathlib import Path
import sys
import uuid

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SERVICE_ROOT = PROJECT_ROOT / "ingestion"
for module_name in list(sys.modules):
    if module_name == "src" or module_name.startswith("src."):
        del sys.modules[module_name]
sys.path.insert(0, str(SERVICE_ROOT))

from src.validation import TelemetryValidationError, validate_telemetry_event


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


def test_validate_telemetry_event_accepts_valid_payload() -> None:
    payload = valid_event()

    validated = validate_telemetry_event(payload)

    assert validated == payload


def test_validate_telemetry_event_allows_missing_flow_reading() -> None:
    payload = valid_event()
    payload["flow_m3_h"] = None
    payload["quality_flag"] = "partial"

    validated = validate_telemetry_event(payload)

    assert validated["flow_m3_h"] is None


def test_validate_telemetry_event_rejects_missing_required_field() -> None:
    payload = valid_event()
    del payload["event_id"]

    with pytest.raises(TelemetryValidationError) as exc_info:
        validate_telemetry_event(payload)

    assert "missing required fields: event_id" in str(exc_info.value)


def test_validate_telemetry_event_rejects_out_of_range_measurement() -> None:
    payload = valid_event()
    payload["anomaly_score"] = 1.5

    with pytest.raises(TelemetryValidationError) as exc_info:
        validate_telemetry_event(payload)

    assert "anomaly_score must be between 0 and 1" in str(exc_info.value)
