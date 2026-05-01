from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
import math
import random
import uuid


@dataclass
class SimulatorState:
    tick: int = 0
    base_temperature: float = 67.0
    base_vibration: float = 2.2
    base_pressure: float = 3.8
    base_rpm: float = 9.6
    base_amperage: float = 410.0
    base_power: float = 4920.0
    base_flow: float = 118.0


@dataclass(frozen=True)
class SimulatedPayload:
    payload: str
    event_id: str | None
    defect_type: str | None = None

    @property
    def is_defective(self) -> bool:
        return self.defect_type is not None


def build_event(
    rng: random.Random,
    state: SimulatorState,
    equipment_id: str,
    site: str,
    line: str,
) -> dict:
    state.tick += 1
    drift = min(state.tick * 0.015, 6.0)
    oscillation = math.sin(state.tick / 8) * 0.8
    anomaly_roll = rng.random()
    missing_roll = rng.random()

    temperature = state.base_temperature + drift + oscillation + rng.uniform(-0.6, 0.6)
    vibration = state.base_vibration + (drift / 6) + rng.uniform(-0.2, 0.2)
    pressure = state.base_pressure - (drift / 12) + rng.uniform(-0.15, 0.15)
    rpm = state.base_rpm + math.sin(state.tick / 10) * 0.25 + rng.uniform(-0.05, 0.05)
    amperage = state.base_amperage + drift * 8 + rng.uniform(-8, 8)
    power = state.base_power + drift * 45 + rng.uniform(-55, 55)
    flow = state.base_flow + math.cos(state.tick / 7) * 1.8 + rng.uniform(-1.0, 1.0)
    operational_state = "running"
    quality_flag = "ok"
    anomaly_score = 0.08 + drift / 20

    if anomaly_roll > 0.96:
        temperature += rng.uniform(8, 13)
        vibration += rng.uniform(1.8, 3.2)
        pressure -= rng.uniform(0.7, 1.1)
        anomaly_score = min(anomaly_score + 0.65, 1.0)
        quality_flag = "anomalous"

    if missing_roll > 0.985:
        flow = None
        quality_flag = "partial"

    if pressure < 2.7 or vibration > 4.8:
        operational_state = "warning"

    if temperature > 82 or pressure < 2.2:
        operational_state = "critical"

    return {
        "event_id": str(uuid.uuid4()),
        "event_ts": datetime.now(UTC).isoformat(),
        "equipment_id": equipment_id,
        "site": site,
        "line": line,
        "operational_state": operational_state,
        "temperature_c": round(temperature, 2),
        "vibration_mm_s": round(vibration, 2),
        "lubrication_pressure_bar": round(pressure, 2),
        "rpm": round(rpm, 2),
        "amperage_a": round(amperage, 2),
        "power_kw": round(power, 2),
        "flow_m3_h": None if flow is None else round(flow, 2),
        "anomaly_score": round(min(anomaly_score, 1.0), 3),
        "quality_flag": quality_flag,
    }


def build_publish_payload(
    rng: random.Random,
    event: dict,
    data_error_rate: float,
) -> SimulatedPayload:
    if rng.random() >= data_error_rate:
        return SimulatedPayload(payload=json.dumps(event), event_id=event["event_id"])

    defect_builder = rng.choice(
        [
            build_malformed_json_payload,
            build_missing_field_payload,
            build_wrong_type_payload,
            build_out_of_range_payload,
            build_invalid_state_payload,
        ]
    )
    return defect_builder(event)


def build_malformed_json_payload(event: dict) -> SimulatedPayload:
    return SimulatedPayload(
        payload=f'{{"event_id": "{event["event_id"]}", "temperature_c": ',
        event_id=event["event_id"],
        defect_type="malformed_json",
    )


def build_missing_field_payload(event: dict) -> SimulatedPayload:
    defective_event = dict(event)
    defective_event.pop("event_id", None)
    return SimulatedPayload(
        payload=json.dumps(defective_event),
        event_id=event["event_id"],
        defect_type="missing_event_id",
    )


def build_wrong_type_payload(event: dict) -> SimulatedPayload:
    defective_event = dict(event)
    defective_event["temperature_c"] = "sensor-overflow"
    return SimulatedPayload(
        payload=json.dumps(defective_event),
        event_id=event["event_id"],
        defect_type="wrong_temperature_type",
    )


def build_out_of_range_payload(event: dict) -> SimulatedPayload:
    defective_event = dict(event)
    defective_event["anomaly_score"] = 1.7
    return SimulatedPayload(
        payload=json.dumps(defective_event),
        event_id=event["event_id"],
        defect_type="out_of_range_anomaly_score",
    )


def build_invalid_state_payload(event: dict) -> SimulatedPayload:
    defective_event = dict(event)
    defective_event["operational_state"] = "unknown"
    return SimulatedPayload(
        payload=json.dumps(defective_event),
        event_id=event["event_id"],
        defect_type="invalid_operational_state",
    )
