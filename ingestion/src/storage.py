from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from psycopg import Connection


CREATE_RAW_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_telemetry (
    id BIGSERIAL PRIMARY KEY,
    event_id TEXT NOT NULL,
    equipment_id TEXT NOT NULL,
    site TEXT NOT NULL,
    line TEXT NOT NULL,
    operational_state TEXT NOT NULL,
    event_ts TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL
);
"""

CREATE_REJECTED_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS rejected_telemetry (
    id BIGSERIAL PRIMARY KEY,
    rejected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reason TEXT NOT NULL,
    topic TEXT,
    raw_payload TEXT NOT NULL,
    decoded_payload JSONB
);
"""

CREATE_INDEXES_SQL = """
CREATE INDEX IF NOT EXISTS idx_raw_telemetry_ingested_at
    ON raw_telemetry (ingested_at);
CREATE INDEX IF NOT EXISTS idx_raw_telemetry_event_ts
    ON raw_telemetry (event_ts);
CREATE INDEX IF NOT EXISTS idx_rejected_telemetry_rejected_at
    ON rejected_telemetry (rejected_at);
"""


INSERT_SQL = """
INSERT INTO raw_telemetry (
    event_id,
    equipment_id,
    site,
    line,
    operational_state,
    event_ts,
    payload
) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb);
"""

INSERT_REJECTED_SQL = """
INSERT INTO rejected_telemetry (
    reason,
    topic,
    raw_payload,
    decoded_payload
) VALUES (%s, %s, %s, %s::jsonb);
"""


def ensure_schema(connection: "Connection") -> None:
    with connection.cursor() as cursor:
        cursor.execute(CREATE_RAW_TABLE_SQL)
        cursor.execute(CREATE_REJECTED_TABLE_SQL)
        cursor.execute(CREATE_INDEXES_SQL)
    connection.commit()


def persist_event(connection: "Connection", payload: dict) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            INSERT_SQL,
            (
                payload["event_id"],
                payload["equipment_id"],
                payload["site"],
                payload["line"],
                payload["operational_state"],
                payload["event_ts"],
                json.dumps(payload),
            ),
        )
    connection.commit()


def persist_rejected_event(
    connection: "Connection",
    *,
    reason: str,
    raw_payload: str,
    decoded_payload: Any = None,
    topic: str | None = None,
) -> None:
    decoded_json = None if decoded_payload is None else json.dumps(decoded_payload)
    with connection.cursor() as cursor:
        cursor.execute(
            INSERT_REJECTED_SQL,
            (
                reason,
                topic,
                raw_payload,
                decoded_json,
            ),
        )
    connection.commit()


def write_bronze_record(output_path: str, payload: dict) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "written_at": datetime.now(UTC).isoformat(),
        "payload": payload,
    }
    with path.open("a", encoding="utf-8") as file_handle:
        file_handle.write(json.dumps(record) + "\n")


def write_dead_letter_record(
    output_path: str,
    *,
    reason: str,
    raw_payload: str,
    decoded_payload: Any = None,
    topic: str | None = None,
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "written_at": datetime.now(UTC).isoformat(),
        "reason": reason,
        "topic": topic,
        "raw_payload": raw_payload,
        "decoded_payload": decoded_payload,
    }
    with path.open("a", encoding="utf-8") as file_handle:
        file_handle.write(json.dumps(record) + "\n")
