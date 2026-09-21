"""Environment-driven configuration with fail-fast on missing required vars."""
import os
import sys
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Settings:
    DASHSCOPE_API_KEY: str
    # RAG retrieval (stage 1.2+) goes directly against a Bailian knowledge
    # base index via the `alibabacloud_bailian20231229` OpenAPI SDK, which
    # uses AccessKey auth (not DASHSCOPE_API_KEY) -- see rag/bailian_kb.py.
    ALIBABA_CLOUD_ACCESS_KEY_ID: str
    ALIBABA_CLOUD_ACCESS_KEY_SECRET: str
    BAILIAN_WORKSPACE_ID: str
    BAILIAN_INDEX_ID: str
    # Deprecated: no longer used for RAG (retrieval now goes straight to the
    # knowledge base index above, bypassing the Bailian "application"
    # concept entirely). Kept optional for backward compatibility / in case
    # a future feature calls dashscope.Application.call directly again.
    BAILIAN_APP_ID: Optional[str] = None
    BAILIAN_RAG_TOP_K: int = 5
    LOG_LEVEL: str = "INFO"
    # Real-world Bailian RAG API latency was observed to range ~1.4s-10.8s;
    # 5s caused frequent silent timeouts that dropped retrieval context. 10s
    # balances responsiveness vs reliability.
    RAG_TIMEOUT_SEC: float = 10.0
    BAILIAN_REGION_ID: str = "cn-beijing"


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        sys.stderr.write(f"ERROR: required environment variable {name} is not set\n")
        sys.exit(1)
    return value


def load_settings() -> Settings:
    return Settings(
        DASHSCOPE_API_KEY=_require("DASHSCOPE_API_KEY"),
        ALIBABA_CLOUD_ACCESS_KEY_ID=_require("ALIBABA_CLOUD_ACCESS_KEY_ID"),
        ALIBABA_CLOUD_ACCESS_KEY_SECRET=_require("ALIBABA_CLOUD_ACCESS_KEY_SECRET"),
        BAILIAN_WORKSPACE_ID=_require("BAILIAN_WORKSPACE_ID"),
        BAILIAN_INDEX_ID=_require("BAILIAN_INDEX_ID"),
        BAILIAN_APP_ID=os.getenv("BAILIAN_APP_ID") or None,
        BAILIAN_RAG_TOP_K=int(os.getenv("BAILIAN_RAG_TOP_K", "5")),
        LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
        RAG_TIMEOUT_SEC=float(os.getenv("RAG_TIMEOUT_SEC", "10.0")),
        BAILIAN_REGION_ID=os.getenv("BAILIAN_REGION_ID", "cn-beijing"),
    )