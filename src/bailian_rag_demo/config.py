"""Environment-driven configuration with fail-fast on missing required vars."""
import os
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    DASHSCOPE_API_KEY: str
    BAILIAN_APP_ID: str
    BAILIAN_RAG_TOP_K: int = 5
    LOG_LEVEL: str = "INFO"
    # Real-world dashscope.Application.call latency for RAG-bound apps was
    # observed to range ~1.4s-10.8s; 5s caused frequent silent timeouts that
    # dropped retrieval context. 10s balances responsiveness vs reliability.
    RAG_TIMEOUT_SEC: float = 10.0


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        sys.stderr.write(f"ERROR: required environment variable {name} is not set\n")
        sys.exit(1)
    return value


def load_settings() -> Settings:
    return Settings(
        DASHSCOPE_API_KEY=_require("DASHSCOPE_API_KEY"),
        BAILIAN_APP_ID=_require("BAILIAN_APP_ID"),
        BAILIAN_RAG_TOP_K=int(os.getenv("BAILIAN_RAG_TOP_K", "5")),
        LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
        RAG_TIMEOUT_SEC=float(os.getenv("RAG_TIMEOUT_SEC", "10.0")),
    )