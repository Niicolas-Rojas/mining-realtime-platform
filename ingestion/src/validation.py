from __future__ import annotations

from datetime import datetime
import math
from typing import Any
from uuid import UUID


ALLOWED_OPERATIONAL_STATES = {"running", "warning", "critical", "stopped", "maintenance"}
ALLOWED_QUALITY_FLAGS = {"ok", "partial", "anomalous"}

REQUIRED_FIELDS = {
    "event_id",
    "event_ts",
    "equipment_id",
    "site",
    "line",
    "operational_state",
    "temperature_c",
    "vibration_mm_s",
    "lubrication_pressure_bar",
    "rpm",
    "amperage_a",
    "power_kw",
    "flow_m3_h",
    "anomaly_score",
    "quality_flag",
}

NUMERIC_RANGES = {
    "temperature_c": (-20.0, 130.0),
    "vibration_mm_s": (0.0, 25.0),
    "lubrication_pressure_bar": (0.0, 10.0),
    "rpm": (0.0, 30.0),
    "amperage_a": (0.0, 2000.0),
    "power_kw": (0.0, 20000.0),
    "flow_m3_h": (0.0, 500.0),
    "anomaly_score": (0.0, 1.0),
}


class TelemetryValidationError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


def validate_telemetry_event(payload: Any) -> dict[str, Any]:
    errors: list[str] = []

    if not isinstance(payload, dict):
        raise TelemetryValidationError(["payload must be a JSON object"])

    missing_fields = sorted(REQUIRED_FIELDS - set(payload))
    if missing_fields:
        errors.append(f"missing required fields: {', '.join(missing_fields)}")

    for field in ("equipment_id", "site", "line"):
        _validate_non_empty_string(payload, field, errors)

    _validate_uuid(payload, "event_id", errors)
    _validate_timestamp(payload, "event_ts", errors)
    _validate_enum(payload, "operational_state", ALLOWED_OPERATIONAL_STATES, errors)
    _validate_enum(payload, "quality_flag", ALLOWED_QUALITY_FLAGS, errors)

    for field, (minimum, maximum) in NUMERIC_RANGES.items():
        allow_null = field == "flow_m3_h"
        _validate_numeric_range(payload, field, minimum, maximum, errors, allow_null=allow_null)

    if errors:
        raise TelemetryValidationError(errors)

    return payload


def _validate_non_empty_string(payload: dict[str, Any], field: str, errors: list[str]) -> None:
    if field not in payload:
        return
    value = payload[field]
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} must be a non-empty string")


def _validate_uuid(payload: dict[str, Any], field: str, errors: list[str]) -> None:
    if field not in payload:
        return
    value = payload[field]
    if not isinstance(value, str):
        errors.append(f"{field} must be a UUID string")
        return
    try:
        UUID(value)
    except ValueError:
        errors.append(f"{field} must be a valid UUID")


def _validate_timestamp(payload: dict[str, Any], field: str, errors: list[str]) -> None:
    if field not in payload:
        return
    value = payload[field]
    if not isinstance(value, str):
        errors.append(f"{field} must be an ISO-8601 timestamp string")
        return
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{field} must be a valid ISO-8601 timestamp")
        return
    if parsed.tzinfo is None:
        errors.append(f"{field} must include timezone information")


def _validate_enum(
    payload: dict[str, Any],
    field: str,
    allowed_values: set[str],
    errors: list[str],
) -> None:
    if field not in payload:
        return
    value = payload[field]
    if not isinstance(value, str) or value not in allowed_values:
        allowed = ", ".join(sorted(allowed_values))
        errors.append(f"{field} must be one of: {allowed}")


def _validate_numeric_range(
    payload: dict[str, Any],
    field: str,
    minimum: float,
    maximum: float,
    errors: list[str],
    *,
    allow_null: bool = False,
) -> None:
    if field not in payload:
        return
    value = payload[field]
    if allow_null and value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        errors.append(f"{field} must be a finite number")
        return
    if not minimum <= float(value) <= maximum:
        errors.append(f"{field} must be between {minimum:g} and {maximum:g}")
