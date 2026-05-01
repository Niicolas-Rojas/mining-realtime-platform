from dataclasses import dataclass
import os


@dataclass(frozen=True)
class IngestionConfig:
    mqtt_broker_host: str = os.getenv("MQTT_BROKER_HOST", "localhost")
    mqtt_broker_port: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    mqtt_topic: str = os.getenv("MQTT_TOPIC", "mining/sag-mill/telemetry")
    mqtt_client_prefix: str = os.getenv("MQTT_CLIENT_PREFIX", "mining-ingestion")
    postgres_db: str = os.getenv("POSTGRES_DB", "mining_rt")
    postgres_user: str = os.getenv("POSTGRES_USER", "mining")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "mining123")
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    bronze_output_path: str = os.getenv(
        "BRONZE_OUTPUT_PATH",
        "/app/data/bronze/raw_telemetry.ndjson",
    )
    dead_letter_output_path: str = os.getenv(
        "DEAD_LETTER_OUTPUT_PATH",
        "/app/data/dead_letter/rejected_telemetry.ndjson",
    )

    @property
    def postgres_dsn(self) -> str:
        return (
            f"dbname={self.postgres_db} user={self.postgres_user} "
            f"password={self.postgres_password} host={self.postgres_host} "
            f"port={self.postgres_port}"
        )
