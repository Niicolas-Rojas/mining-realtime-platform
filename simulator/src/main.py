from __future__ import annotations

import logging
import random
import time

from paho.mqtt import client as mqtt

from config import SimulatorConfig
from payloads import SimulatorState, build_event, build_publish_payload


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [simulator] %(message)s",
)


def build_client(config: SimulatorConfig) -> mqtt.Client:
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"{config.mqtt_client_prefix}-{config.equipment_id}",
    )
    for attempt in range(1, 21):
        try:
            client.connect(config.mqtt_broker_host, config.mqtt_broker_port, 60)
            logging.info("connected to mqtt on attempt=%s", attempt)
            return client
        except Exception as exc:  # pragma: no cover - startup retry path
            logging.warning("mqtt not ready attempt=%s error=%s", attempt, exc)
            time.sleep(2)
    raise RuntimeError("could not connect to mqtt broker")


def main() -> None:
    config = SimulatorConfig()
    rng = random.Random(config.random_seed)
    state = SimulatorState()
    client = build_client(config)
    client.loop_start()

    logging.info(
        "publishing telemetry to topic=%s broker=%s:%s",
        config.mqtt_topic,
        config.mqtt_broker_host,
        config.mqtt_broker_port,
    )

    try:
        while True:
            event = build_event(
                rng=rng,
                state=state,
                equipment_id=config.equipment_id,
                site=config.site,
                line=config.line,
            )
            publish_payload = build_publish_payload(
                rng=rng,
                event=event,
                data_error_rate=config.data_error_rate,
            )
            result = client.publish(config.mqtt_topic, publish_payload.payload, qos=1)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logging.warning("publish failed rc=%s event_id=%s", result.rc, event["event_id"])
            elif publish_payload.is_defective:
                logging.info(
                    "published defective event_id=%s defect_type=%s",
                    publish_payload.event_id,
                    publish_payload.defect_type,
                )
            else:
                logging.info(
                    "published event_id=%s state=%s temp=%s anomaly=%s",
                    event["event_id"],
                    event["operational_state"],
                    event["temperature_c"],
                    event["anomaly_score"],
                )
            time.sleep(config.interval_seconds)
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
