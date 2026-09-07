"""Environment and filesystem settings.

Secrets stay in .env. Nothing in the benchmark artifacts writes API keys back out.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be numeric") from exc


@dataclass(frozen=True)
class Settings:
    root: Path = ROOT
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "")
    openai_responses_endpoint: str = os.getenv("OPENAI_RESPONSES_ENDPOINT", "https://api.openai.com/v1/responses")
    openai_input_usd_per_million: float = _float("OPENAI_INPUT_USD_PER_MILLION", 0.0)
    openai_cached_input_usd_per_million: float = _float("OPENAI_CACHED_INPUT_USD_PER_MILLION", 0.0)
    openai_output_usd_per_million: float = _float("OPENAI_OUTPUT_USD_PER_MILLION", 0.0)
    serper_api_key: str = os.getenv("SERPER_API_KEY", "")
    serper_endpoint: str = os.getenv("SERPER_ENDPOINT", "https://google.serper.dev/search")
    serper_usd_per_1000_searches: float = _float("SERPER_USD_PER_1000_SEARCHES", 0.0)
    http_user_agent: str = os.getenv("HTTP_USER_AGENT", "SmartAIAgents-Book-Experiment/1.0")
    http_timeout_seconds: float = _float("HTTP_TIMEOUT_SECONDS", 20.0)
    playwright_timeout_ms: float = _float("PLAYWRIGHT_TIMEOUT_MS", 20000.0)
    capability_dir: Path = ROOT / os.getenv("CAPABILITY_DIR", "capabilities/registry")
    ledger_dir: Path = ROOT / os.getenv("LEDGER_DIR", "benchmark/results")
    benchmark_site_host: str = os.getenv("BENCHMARK_SITE_HOST", "127.0.0.1")
    benchmark_site_port: int = int(os.getenv("BENCHMARK_SITE_PORT", "8765"))

    def validate_openai(self) -> None:
        if not self.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for --provider openai")
        if not self.openai_model:
            raise RuntimeError(
                "OPENAI_MODEL is required. Choose a current model in your account that "
                "supports the Responses API and Structured Outputs."
            )


settings = Settings()
