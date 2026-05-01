import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SERVICE_ROOT = PROJECT_ROOT / "ingestion"
for module_name in list(sys.modules):
    if module_name == "src" or module_name.startswith("src."):
        del sys.modules[module_name]
sys.path.insert(0, str(SERVICE_ROOT))

from src.storage import persist_rejected_event, write_bronze_record, write_dead_letter_record


def test_write_bronze_record_creates_ndjson(tmp_path) -> None:
    target = tmp_path / "bronze" / "raw.ndjson"
    payload = {"event_id": "evt-1", "temperature_c": 70.1}

    write_bronze_record(str(target), payload)

    lines = target.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["payload"]["event_id"] == "evt-1"


def test_write_dead_letter_record_creates_ndjson(tmp_path) -> None:
    target = tmp_path / "dead_letter" / "rejected.ndjson"

    write_dead_letter_record(
        str(target),
        reason="schema_validation_failed: missing required fields: event_id",
        raw_payload='{"temperature_c": 70.1}',
        decoded_payload={"temperature_c": 70.1},
        topic="mining/sag-mill/telemetry",
    )

    lines = target.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["reason"].startswith("schema_validation_failed")
    assert record["topic"] == "mining/sag-mill/telemetry"
    assert record["decoded_payload"]["temperature_c"] == 70.1


def test_persist_rejected_event_inserts_expected_values() -> None:
    calls = []

    class Cursor:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def execute(self, sql, params):
            calls.append((sql, params))

    class Connection:
        def cursor(self):
            return Cursor()

        def commit(self):
            calls.append(("commit", None))

    persist_rejected_event(
        Connection(),
        reason="invalid_json: syntax",
        raw_payload="{not-json",
        decoded_payload=None,
        topic="mining/sag-mill/telemetry",
    )

    assert calls[0][1] == (
        "invalid_json: syntax",
        "mining/sag-mill/telemetry",
        "{not-json",
        None,
    )
    assert calls[1] == ("commit", None)
