from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SERVICE_ROOT = PROJECT_ROOT / "api"
for module_name in list(sys.modules):
    if module_name == "src" or module_name.startswith("src."):
        del sys.modules[module_name]
sys.path.insert(0, str(SERVICE_ROOT))

from src import main as api_main
from src.main import health, pipeline_metrics


def test_health_endpoint_payload() -> None:
    payload = health()
    assert payload["status"] == "ok"
    assert payload["service"] == "api"


def test_pipeline_metrics_endpoint_payload(monkeypatch) -> None:
    monkeypatch.setattr(
        api_main,
        "fetch_pipeline_metrics",
        lambda _config: {"accepted_events": 10, "invalid_events_dead_lettered": 1},
    )

    payload = pipeline_metrics()

    assert payload["metrics"]["accepted_events"] == 10
    assert payload["metrics"]["invalid_events_dead_lettered"] == 1
