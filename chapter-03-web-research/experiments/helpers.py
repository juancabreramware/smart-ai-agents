"""Small helpers shared by experiment entry points."""
from pathlib import Path
from smart_agent.models import TaskDescriptor
from smart_agent.settings import settings

ROOT = Path(__file__).resolve().parents[1]


def controlled_task(host: str | None = None, port: int | None = None) -> TaskDescriptor:
    host = host or settings.benchmark_site_host
    port = port or settings.benchmark_site_port
    url = f"http://{host}:{port}/pricing"
    return TaskDescriptor(
        vendor_id="northstar-cloud-controlled",
        vendor_name="Northstar Cloud",
        domain=host,
        pricing_url=url,
    )


def ground_truth(version: str) -> Path:
    return ROOT / "benchmark_site" / "ground_truth" / f"{version}.json"
