from pathlib import Path
import random
import sys
import json


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SERVICE_ROOT = PROJECT_ROOT / "simulator"
for module_name in list(sys.modules):
    if module_name == "src" or module_name.startswith("src."):
        del sys.modules[module_name]
sys.path.insert(0, str(SERVICE_ROOT))

from src.payloads import SimulatorState, build_event, build_publish_payload


def test_build_event_contains_expected_fields() -> None:
    event = build_event(
        rng=random.Random(42),
        state=SimulatorState(),
        equipment_id="sag-mill-01",
        site="site-a",
        line="line-1",
    )

    assert event["equipment_id"] == "sag-mill-01"
    assert event["site"] == "site-a"
    assert event["line"] == "line-1"
    assert 0 <= event["anomaly_score"] <= 1
    assert "event_id" in event
    assert "event_ts" in event


def test_build_publish_payload_keeps_valid_event_when_error_rate_is_zero() -> None:
    event = build_event(
        rng=random.Random(42),
        state=SimulatorState(),
        equipment_id="sag-mill-01",
        site="site-a",
        line="line-1",
    )

    payload = build_publish_payload(
        rng=random.Random(42),
        event=event,
        data_error_rate=0.0,
    )

    assert payload.is_defective is False
    assert json.loads(payload.payload)["event_id"] == event["event_id"]


def test_build_publish_payload_can_emit_defective_event() -> None:
    event = build_event(
        rng=random.Random(42),
        state=SimulatorState(),
        equipment_id="sag-mill-01",
        site="site-a",
        line="line-1",
    )

    payload = build_publish_payload(
        rng=random.Random(7),
        event=event,
        data_error_rate=1.0,
    )

    assert payload.is_defective is True
    assert payload.defect_type in {
        "malformed_json",
        "missing_event_id",
        "wrong_temperature_type",
        "out_of_range_anomaly_score",
        "invalid_operational_state",
    }
