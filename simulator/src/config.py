from dataclasses import dataclass
import os


@dataclass(frozen=True)
class SimulatorConfig:
    mqtt_broker_host: str = os.getenv("MQTT_BROKER_HOST", "localhost")
    mqtt_broker_port: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    mqtt_topic: str = os.getenv("MQTT_TOPIC", "mining/sag-mill/telemetry")
    mqtt_client_prefix: str = os.getenv("MQTT_CLIENT_PREFIX", "mining-simulator")
    mqtt_username: str = os.getenv("MQTT_USERNAME", "")
    mqtt_password: str = os.getenv("MQTT_PASSWORD", "")
    mqtt_use_tls: bool = os.getenv("MQTT_USE_TLS", "false").lower() == "true"
    equipment_id: str = os.getenv("SIMULATOR_EQUIPMENT_ID", "sag-mill-01")
    site: str = os.getenv("SIMULATOR_SITE", "concentradora-norte")
    line: str = os.getenv("SIMULATOR_LINE", "linea-a")
    interval_seconds: float = float(os.getenv("SIMULATOR_INTERVAL_SECONDS", "2.0"))
    random_seed: int = int(os.getenv("SIMULATOR_RANDOM_SEED", "42"))
    data_error_rate: float = float(os.getenv("SIMULATOR_DATA_ERROR_RATE", "0.03"))
