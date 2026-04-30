"""Runtime configuration loaded from environment variables.

API keys and tunable values live in a .env file at the project root,
never in code, so secrets do not end up in version control and so the
same code runs in different environments without changes.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    """Frozen so it cannot be mutated after load(), which prevents
    one module accidentally changing config seen by another."""

    openai_api_key: str
    serpapi_key: str
    openai_model: str
    relevance_threshold: int
    output_dir: Path


def load_config() -> Config:
    """Read environment variables and return a validated Config.

    Raises ValueError if required keys are missing, because running
    the agent without keys would only fail later inside an API call
    with a less helpful error message.
    """
    load_dotenv()

    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    serpapi_key = os.getenv("SERPAPI_KEY", "").strip()

    if not openai_key:
        raise ValueError(
            "OPENAI_API_KEY is missing. Copy .env.example to .env and fill it in."
        )
    if not serpapi_key:
        raise ValueError(
            "SERPAPI_KEY is missing. Copy .env.example to .env and fill it in."
        )

    threshold_raw = os.getenv("RELEVANCE_THRESHOLD", "60")
    try:
        threshold = int(threshold_raw)
    except ValueError as exc:
        raise ValueError(
            f"RELEVANCE_THRESHOLD must be an integer, got {threshold_raw!r}"
        ) from exc

    if not 0 <= threshold <= 100:
        raise ValueError(
            f"RELEVANCE_THRESHOLD must be between 0 and 100, got {threshold}"
        )

    return Config(
        openai_api_key=openai_key,
        serpapi_key=serpapi_key,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        relevance_threshold=threshold,
        output_dir=Path(os.getenv("OUTPUT_DIR", "./output")).resolve(),
    )
