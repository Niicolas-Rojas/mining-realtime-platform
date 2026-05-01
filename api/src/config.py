from dataclasses import dataclass
import os


@dataclass(frozen=True)
class ApiConfig:
    postgres_db: str = os.getenv("POSTGRES_DB", "mining_rt")
    postgres_user: str = os.getenv("POSTGRES_USER", "mining")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "mining123")
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_sslmode: str = os.getenv("POSTGRES_SSLMODE", "")

    @property
    def postgres_dsn(self) -> str:
        dsn = (
            f"dbname={self.postgres_db} user={self.postgres_user} "
            f"password={self.postgres_password} host={self.postgres_host} "
            f"port={self.postgres_port}"
        )
        if self.postgres_sslmode:
            dsn += f" sslmode={self.postgres_sslmode}"
        return dsn
