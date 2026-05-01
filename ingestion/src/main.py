from __future__ import annotations

import json
import logging
import time
from typing import Any

from paho.mqtt import client as mqtt
from psycopg import connect
from psycopg.connection import Connection

from src.config import IngestionConfig
from src.storage import (
    ensure_schema,
    persist_event,
    persist_rejected_event,
    write_bronze_record,
    write_dead_letter_record,
)
from src.validation import TelemetryValidationError, validate_telemetry_event


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [ingestion] %(message)s",
)


def connect_postgres(config: IngestionConfig, retries: int = 20, delay: float = 2.0) -> Connection:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            connection = connect(config.postgres_dsn)
            ensure_schema(connection)
            logging.info("connected to postgres on attempt=%s", attempt)
            return connection
        except Exception as exc:  # pragma: no cover - startup retry path
            last_error = exc
            logging.warning("postgres not ready attempt=%s error=%s", attempt, exc)
            time.sleep(delay)
    raise RuntimeError("could not connect to postgres") from last_error


def build_client(config: IngestionConfig, connection: Connection) -> mqtt.Client:
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"{config.mqtt_client_prefix}-consumer",
    )

    def on_connect(
        mqtt_client: mqtt.Client,
        _userdata: object,
        _flags: dict,
        reason_code: mqtt.ReasonCode,
        _properties: mqtt.Properties | None,
    ) -> None:
        logging.info("connected to mqtt reason_code=%s", reason_code)
        mqtt_client.subscribe(config.mqtt_topic, qos=1)

    def on_message(
        _mqtt_client: mqtt.Client,
        _userdata: object,
        message: mqtt.MQTTMessage,
    ) -> None:
        process_message_payload(
            raw_payload=message.payload,
            config=config,
            connection=connection,
            topic=message.topic,
        )

    client.on_connect = on_connect
    client.on_message = on_message
    if config.mqtt_username:
        client.username_pw_set(config.mqtt_username, config.mqtt_password)
    if config.mqtt_use_tls:
        client.tls_set()
    for attempt in range(1, 21):
        try:
            client.connect(config.mqtt_broker_host, config.mqtt_broker_port, 60)
            logging.info("connected to mqtt broker on attempt=%s", attempt)
            return client
        except Exception as exc:  # pragma: no cover - startup retry path
            logging.warning("mqtt not ready attempt=%s error=%s", attempt, exc)
            time.sleep(2)
    raise RuntimeError("could not connect to mqtt broker")


def process_message_payload(
    *,
    raw_payload: bytes,
    config: IngestionConfig,
    connection: Connection,
    topic: str | None = None,
) -> bool:
    raw_text = raw_payload.decode("utf-8", errors="replace")
    try:
        decoded_payload: Any = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        reason = f"invalid_json: {exc.msg}"
        dead_letter_event(
            config,
            connection=connection,
            reason=reason,
            raw_payload=raw_text,
            topic=topic,
        )
        logging.warning("dead-lettered invalid json reason=%s", reason)
        return False

    try:
        payload = validate_telemetry_event(decoded_payload)
    except TelemetryValidationError as exc:
        reason = f"schema_validation_failed: {exc}"
        dead_letter_event(
            config,
            connection=connection,
            reason=reason,
            raw_payload=raw_text,
            decoded_payload=decoded_payload,
            topic=topic,
        )
        logging.warning("dead-lettered invalid telemetry reason=%s", reason)
        return False

    persist_event(connection, payload)
    write_bronze_record(config.bronze_output_path, payload)
    logging.info(
        "ingested event_id=%s state=%s temp=%s",
        payload["event_id"],
        payload["operational_state"],
        payload["temperature_c"],
    )
    return True


def dead_letter_event(
    config: IngestionConfig,
    *,
    connection: Connection,
    reason: str,
    raw_payload: str,
    decoded_payload: Any = None,
    topic: str | None = None,
) -> None:
    try:
        persist_rejected_event(
            connection,
            reason=reason,
            raw_payload=raw_payload,
            decoded_payload=decoded_payload,
            topic=topic,
        )
    except Exception:
        logging.exception("failed to persist rejected event")

    try:
        write_dead_letter_record(
            config.dead_letter_output_path,
            reason=reason,
            raw_payload=raw_payload,
            decoded_payload=decoded_payload,
            topic=topic,
        )
    except Exception:
        logging.exception("failed to write dead-letter file")


def main() -> None:
    config = IngestionConfig()
    connection = connect_postgres(config)
    client = build_client(config, connection)
    client.loop_forever()


if __name__ == "__main__":
    main()
