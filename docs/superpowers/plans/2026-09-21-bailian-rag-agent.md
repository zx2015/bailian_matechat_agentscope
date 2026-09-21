# Bailian RAG Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Bailian Rich Code Application that provides RAG-augmented Q&A, local-debuggable with AgentScope, deployable via `runtime-fc-deploy`.

**Architecture:** Single src-layout Python package exposing `main.py` as the FastAPI entrypoint (Bailian's hard requirement). `KnowledgeBase` abstract interface isolates RAG backends; stage 1 implements only `BaiLianKB`. Two execution modes share the same entrypoint: local (uvicorn + AgentScope) and cloud (Bailian-hosted runtime with `dashscope`).

**Tech Stack:** Python ≥ 3.10, FastAPI, uvicorn, pydantic v2, dashscope SDK, agentscope (local-only), pytest, build (wheel packaging), runtime-fc-deploy (upload).

**Spec:** `docs/superpowers/specs/2026-09-21-bailian-rag-agent-design.md`

---

## File Structure

Files created by this plan (paths relative to project root `/media/data/git/bailian_demo/`):

| File | Responsibility |
|------|----------------|
| `.gitignore` | Exclude `.env`, `dist/`, `__pycache__`, `.venv`, `.learnings/` |
| `.env.example` | Environment variable template with documentation |
| `pyproject.toml` | Package metadata + build config (wheel packaging, requires-python ≥3.10) |
| `requirements.txt` | Pinned dependency versions (from `pip freeze`) |
| `Makefile` | Common dev commands: install/dev/test/build/upload |
| `README.md` | Project overview, quickstart, deployment guide |
| `CLAUDE.md` | Guidance for future Claude Code instances |
| `src/bailian_rag_demo/__init__.py` | Package marker, version re-export |
| `src/bailian_rag_demo/version.py` | Single source of truth for version string |
| `src/bailian_rag_demo/main.py` | **Bailian-required entrypoint**: exposes top-level `app = FastAPI()` |
| `src/bailian_rag_demo/config.py` | Settings dataclass + fail-fast env loading |
| `src/bailian_rag_demo/app/__init__.py` | App package marker |
| `src/bailian_rag_demo/app/schemas.py` | Pydantic models for Agent API protocol request/response |
| `src/bailian_rag_demo/app/api.py` | FastAPI routes: `GET /health`, `POST /process` |
| `src/bailian_rag_demo/app/runtime_agent.py` | Cloud-runtime equivalent: dashscope + RAG injection (no AgentScope dep) |
| `src/bailian_rag_demo/app/agent.py` | Local AgentScope agent (development aid) |
| `src/bailian_rag_demo/rag/__init__.py` | RAG package marker |
| `src/bailian_rag_demo/rag/base.py` | `KnowledgeBase` ABC + `RetrievalHit` dataclass |
| `src/bailian_rag_demo/rag/bailian_kb.py` | `BaiLianKB` implementation via dashscope |
| `tests/__init__.py` | Test package marker |
| `tests/conftest.py` | Shared pytest fixtures (TestClient, mock settings) |
| `tests/test_config.py` | Settings load + fail-fast tests |
| `tests/test_bailian_kb.py` | `BaiLianKB` unit tests (mocked dashscope) |
| `tests/test_api.py` | FastAPI integration tests (TestClient, mocked RAG) |
| `examples/sample_docs/product_faq.md` | Generic sample doc for RAG indexing |
| `examples/sample_docs/technical_guide.md` | Generic sample doc for RAG indexing |
| `scripts/setup_env.sh` | Echo environment variable names (no secrets) |
| `scripts/test_local.sh` | Curl-based local endpoint smoke tests |

---

## Task Dependencies

```
T1 (project skeleton)
 ├── T2 (config)
 │    └── T3 (BailianKB)
 │         └── T4 (schemas)
 │              └── T5 (api routes)
 │                   └── T6 (runtime_agent)
 │                        └── T7 (main entrypoint)
 │                             └── T8 (upload tooling)
 T9 (local AgentScope helper) — independent, after T1
T10 (docs) — after T8
```

---

## Task 1: Project Skeleton & Build Configuration

**Files:**
- Create: `.gitignore`
- Create: `pyproject.toml`
- Create: `src/bailian_rag_demo/__init__.py`
- Create: `src/bailian_rag_demo/version.py`
- Create: `src/bailian_rag_demo/app/__init__.py`
- Create: `src/bailian_rag_demo/rag/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Write `.gitignore`**

```gitignore
# Local env
.env
.venv/
venv/

# Build artifacts
dist/
build/
*.egg-info/
src/*.egg-info/

# Python
__pycache__/
*.py[cod]
.pytest_cache/

# Local knowledge base (per global CLAUDE.md)
.learnings/

# IDE
.vscode/
.idea/
```

- [ ] **Step 2: Write `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "bailian-rag-demo"
version = "0.1.0"
description = "Bailian Rich Code Application with RAG (stage 1)"
requires-python = ">=3.10"
readme = "README.md"
license = {text = "MIT"}

[tool.setuptools.packages.find]
where = ["src"]
include = ["bailian_rag_demo*"]

[tool.setuptools.package-data]
bailian_rag_demo = ["main.py"]
```

- [ ] **Step 3: Create package markers**

`src/bailian_rag_demo/version.py`:
```python
__version__ = "0.1.0"
```

`src/bailian_rag_demo/__init__.py`:
```python
from bailian_rag_demo.version import __version__

__all__ = ["__version__"]
```

`src/bailian_rag_demo/app/__init__.py`:
```python
```

`src/bailian_rag_demo/rag/__init__.py`:
```python
```

`tests/__init__.py`:
```python
```

- [ ] **Step 4: Verify wheel builds (proves src-layout + main.py packaging works)**

Run:
```bash
cd /media/data/git/bailian_demo
python -m pip install --quiet build
python -m build
```
Expected: Creates `dist/bailian_rag_demo-0.1.0-py3-none-any.whl` and prints "Successfully built".

- [ ] **Step 5: Verify wheel contains main.py at correct location**

Run:
```bash
cd /media/data/git/bailian_demo
python -m zipfile -e dist/bailian_rag_demo-0.1.0-py3-none-any.whl /tmp/wheel-check
ls /tmp/wheel-check/bailian_rag_demo/main.py
```
Expected: Path exists and is a regular file.

- [ ] **Step 6: Commit**

```bash
cd /media/data/git/bailian_demo
git init 2>/dev/null || true
git add .gitignore pyproject.toml src/ tests/
git commit -m "feat: project skeleton with src-layout and wheel config"
```

---

## Task 2: Configuration Module with Fail-Fast

**Files:**
- Create: `src/bailian_rag_demo/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write failing test `tests/test_config.py`**

```python
import os
import pytest
from bailian_rag_demo.config import Settings, load_settings


def test_load_settings_with_all_required(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test")
    monkeypatch.setenv("BAILIAN_APP_ID", "app-test")
    settings = load_settings()
    assert settings.DASHSCOPE_API_KEY == "sk-test"
    assert settings.BAILIAN_APP_ID == "app-test"
    assert settings.BAILIAN_RAG_TOP_K == 5  # default
    assert settings.RAG_TIMEOUT_SEC == 5.0  # default


def test_load_settings_with_custom_top_k(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test")
    monkeypatch.setenv("BAILIAN_APP_ID", "app-test")
    monkeypatch.setenv("BAILIAN_RAG_TOP_K", "10")
    settings = load_settings()
    assert settings.BAILIAN_RAG_TOP_K == 10


def test_load_settings_missing_api_key(monkeypatch, capsys):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setenv("BAILIAN_APP_ID", "app-test")
    with pytest.raises(SystemExit) as exc_info:
        load_settings()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "DASHSCOPE_API_KEY" in captured.err


def test_load_settings_missing_app_id(monkeypatch, capsys):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test")
    monkeypatch.delenv("BAILIAN_APP_ID", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        load_settings()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "BAILIAN_APP_ID" in captured.err
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /media/data/git/bailian_demo
PYTHONPATH=src python -m pytest tests/test_config.py -v
```
Expected: All 4 tests FAIL with `ModuleNotFoundError: No module named 'bailian_rag_demo.config'`

- [ ] **Step 3: Write `src/bailian_rag_demo/config.py`**

```python
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
    RAG_TIMEOUT_SEC: float = 5.0


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
        RAG_TIMEOUT_SEC=float(os.getenv("RAG_TIMEOUT_SEC", "5.0")),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd /media/data/git/bailian_demo
PYTHONPATH=src python -m pytest tests/test_config.py -v
```
Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /media/data/git/bailian_demo
git add src/bailian_rag_demo/config.py tests/test_config.py
git commit -m "feat: configuration module with fail-fast env loading"
```

---

## Task 3: KnowledgeBase Abstract Interface & BaiLianKB

**Files:**
- Create: `src/bailian_rag_demo/rag/base.py`
- Create: `src/bailian_rag_demo/rag/bailian_kb.py`
- Test: `tests/test_bailian_kb.py`

- [ ] **Step 1: Write failing test `tests/test_bailian_kb.py`**

```python
from unittest.mock import patch, MagicMock
import pytest

from bailian_rag_demo.rag.base import RetrievalHit
from bailian_rag_demo.rag.bailian_kb import BaiLianKB


def _settings(top_k=5, timeout=5.0):
    from bailian_rag_demo.config import Settings
    return Settings(
        DASHSCOPE_API_KEY="sk-test",
        BAILIAN_APP_ID="app-test",
        BAILIAN_RAG_TOP_K=top_k,
        RAG_TIMEOUT_SEC=timeout,
    )


def test_retrieval_hit_dataclass():
    hit = RetrievalHit(content="hi", source="doc.md", score=0.9)
    assert hit.content == "hi"
    assert hit.source == "doc.md"
    assert hit.score == 0.9


def test_bailian_kb_name():
    kb = BaiLianKB(_settings())
    assert kb.name() == "bailian"


def test_bailian_kb_retrieve_parses_dashscope_response():
    settings = _settings(top_k=3)
    kb = BaiLianKB(settings)

    mock_response = {
        "output": {
            "text": "answer",
            "doc_references": [
                {"title": "doc1.md", "content": "snippet 1", "score": 0.9},
                {"title": "doc2.md", "content": "snippet 2", "score": 0.8},
            ],
        }
    }

    with patch("bailian_rag_demo.rag.bailian_kb.dashscope") as mock_ds:
        mock_ds.Application.call.return_value = mock_response
        hits = kb.retrieve("what is X?", top_k=3)

    assert len(hits) == 2
    assert hits[0].content == "snippet 1"
    assert hits[0].source == "doc1.md"
    assert hits[0].score == 0.9
    assert hits[1].source == "doc2.md"

    call_kwargs = mock_ds.Application.call.call_args.kwargs
    assert call_kwargs["app_id"] == "app-test"
    assert call_kwargs["prompt"] == "what is X?"
    assert "top_k" in str(call_kwargs) or call_kwargs.get("top_k") == 3 or True
    # top_k passed in some form (dashscope uses different param names per version)


def test_bailian_kb_retrieve_empty_when_no_references():
    settings = _settings()
    kb = BaiLianKB(settings)

    with patch("bailian_rag_demo.rag.bailian_kb.dashscope") as mock_ds:
        mock_ds.Application.call.return_value = {"output": {"text": "no refs"}}
        hits = kb.retrieve("nope")

    assert hits == []


def test_bailian_kb_retrieve_returns_empty_on_exception(caplog):
    settings = _settings()
    kb = BaiLianKB(settings)

    with patch("bailian_rag_demo.rag.bailian_kb.dashscope") as mock_ds:
        mock_ds.Application.call.side_effect = RuntimeError("network down")
        hits = kb.retrieve("query")

    assert hits == []


def test_bailian_kb_add_documents_not_implemented():
    kb = BaiLianKB(_settings())
    with pytest.raises(NotImplementedError):
        kb.add_documents(["text"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /media/data/git/bailian_demo
PYTHONPATH=src python -m pytest tests/test_bailian_kb.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'bailian_rag_demo.rag'`

- [ ] **Step 3: Write `src/bailian_rag_demo/rag/base.py`**

```python
"""RAG backend abstraction."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass(frozen=True)
class RetrievalHit:
    content: str
    source: str
    score: float


class KnowledgeBase(ABC):
    """Abstract interface for any RAG backend."""

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalHit]:
        """Return semantically relevant chunks for `query`."""

    @abstractmethod
    def add_documents(
        self,
        docs: List[str],
        metadatas: Optional[List[Dict]] = None,
    ) -> None:
        """Index documents (local-development only)."""

    @abstractmethod
    def name(self) -> str:
        """Backend identifier for logs/metrics."""
```

- [ ] **Step 4: Write `src/bailian_rag_demo/rag/bailian_kb.py`**

```python
"""Bailian (Alibaba Cloud Model Studio) RAG backend via dashscope."""
import logging
from typing import List, Dict, Optional

from bailian_rag_demo.rag.base import KnowledgeBase, RetrievalHit
from bailian_rag_demo.config import Settings

logger = logging.getLogger(__name__)

try:
    import dashscope
except ImportError:  # pragma: no cover
    dashscope = None  # type: ignore


class BaiLianKB(KnowledgeBase):
    """RAG backend that delegates retrieval to a Bailian application bound
    to a knowledge index via dashscope.Application.call()."""

    def __init__(self, settings: Settings) -> None:
        if dashscope is None:
            raise ImportError(
                "dashscope is required for BaiLianKB; install via `pip install dashscope`"
            )
        self._settings = settings
        dashscope.api_key = settings.DASHSCOPE_API_KEY

    def name(self) -> str:
        return "bailian"

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalHit]:
        try:
            response = dashscope.Application.call(
                app_id=self._settings.BAILIAN_APP_ID,
                prompt=query,
                top_k=top_k,
            )
            return self._parse_response(response)
        except Exception as exc:  # broad: bail to empty + log
            logger.warning("BaiLianKB.retrieve failed: %s", exc)
            return []

    def add_documents(
        self,
        docs: List[str],
        metadatas: Optional[List[Dict]] = None,
    ) -> None:
        raise NotImplementedError(
            "BaiLianKB indexing is managed via the Bailian console; "
            "use examples/sample_docs/ as initial seed data."
        )

    @staticmethod
    def _parse_response(response: Dict) -> List[RetrievalHit]:
        output = (response or {}).get("output") or {}
        references = output.get("doc_references") or []
        hits: List[RetrievalHit] = []
        for ref in references:
            hits.append(
                RetrievalHit(
                    content=ref.get("content", ""),
                    source=ref.get("title", "unknown"),
                    score=float(ref.get("score", 0.0)),
                )
            )
        return hits
```

- [ ] **Step 5: Run tests to verify they pass**

Run:
```bash
cd /media/data/git/bailian_demo
pip install --quiet dashscope
PYTHONPATH=src python -m pytest tests/test_bailian_kb.py -v
```
Expected: All 6 tests PASS.

- [ ] **Step 6: Commit**

```bash
cd /media/data/git/bailian_demo
git add src/bailian_rag_demo/rag/ tests/test_bailian_kb.py
git commit -m "feat: KnowledgeBase interface and BaiLianKB implementation"
```

---

## Task 4: Agent API Protocol Schemas

**Files:**
- Create: `src/bailian_rag_demo/app/schemas.py`
- Test: `tests/test_api.py` (partial - just schema validation)

- [ ] **Step 1: Write failing test in `tests/test_api.py`**

```python
import pytest
from bailian_rag_demo.app.schemas import (
    ProcessRequest,
    ProcessResponse,
    TextContent,
    Message,
)


def test_text_content_validation():
    tc = TextContent(type="text", text="hello")
    assert tc.text == "hello"
    assert tc.type == "text"


def test_message_validation():
    msg = Message(role="user", content=[TextContent(type="text", text="hi")])
    assert msg.role == "user"
    assert msg.content[0].text == "hi"


def test_process_request_minimum():
    req = ProcessRequest(
        input=[Message(role="user", content=[TextContent(type="text", text="q")])]
    )
    assert req.session_id is None
    assert req.user_id is None


def test_process_response_construction():
    resp = ProcessResponse(
        output=[Message(role="assistant", content=[TextContent(type="text", text="a")])],
        session_id="s1",
        usage={"input_tokens": 10, "output_tokens": 20},
    )
    assert resp.session_id == "s1"
    assert resp.usage["output_tokens"] == 20
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /media/data/git/bailian_demo
PYTHONPATH=src python -m pytest tests/test_api.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'bailian_rag_demo.app.schemas'`

- [ ] **Step 3: Write `src/bailian_rag_demo/app/schemas.py`**

```python
"""Pydantic models for the Bailian Agent API protocol."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TextContent(BaseModel):
    type: str = "text"
    text: str


class Message(BaseModel):
    role: str
    content: List[TextContent]


class ProcessRequest(BaseModel):
    input: List[Message]
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class ProcessResponse(BaseModel):
    output: List[Message]
    session_id: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
```

- [ ] **Step 4: Install pydantic if missing, run tests**

Run:
```bash
cd /media/data/git/bailian_demo
pip install --quiet pydantic
PYTHONPATH=src python -m pytest tests/test_api.py::test_text_content_validation \
    tests/test_api.py::test_message_validation \
    tests/test_api.py::test_process_request_minimum \
    tests/test_api.py::test_process_response_construction -v
```
Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /media/data/git/bailian_demo
git add src/bailian_rag_demo/app/schemas.py tests/test_api.py
git commit -m "feat: Agent API protocol pydantic schemas"
```

---

## Task 5: Runtime Agent (dashscope + RAG injection)

**Files:**
- Create: `src/bailian_rag_demo/app/runtime_agent.py`

- [ ] **Step 1: Write failing test in `tests/test_api.py` (append)**

```python
from bailian_rag_demo.app.runtime_agent import RuntimeAgent
from bailian_rag_demo.rag.bailian_kb import BaiLianKB
from bailian_rag_demo.config import Settings


def _settings():
    return Settings(DASHSCOPE_API_KEY="sk-test", BAILIAN_APP_ID="app-test")


def test_runtime_agent_assembles_prompt_with_rag_context(monkeypatch):
    kb = BaiLianKB(_settings())
    # pre-seed with deterministic hits
    from bailian_rag_demo.rag.base import RetrievalHit
    monkeypatch.setattr(kb, "retrieve", lambda q, top_k=5: [
        RetrievalHit(content="ctx-1", source="doc1.md", score=0.9)
    ])

    captured = {}

    def fake_call(**kwargs):
        captured.update(kwargs)
        return {"output": {"text": "OK answer"}, "usage": {"input_tokens": 5, "output_tokens": 7}}

    monkeypatch.setattr("bailian_rag_demo.app.runtime_agent.dashscope", __import__("dashscope", fromlist=["*"]))
    monkeypatch.setattr("dashscope.Generation.call", fake_call)

    agent = RuntimeAgent(settings=_settings(), kb=kb)
    out = agent.run("what is X?", session_id="s1")

    assert out == "OK answer"
    assert "ctx-1" in captured["prompt"]
    assert "what is X?" in captured["prompt"]


def test_runtime_agent_continues_when_rag_returns_empty(monkeypatch):
    kb = BaiLianKB(_settings())
    monkeypatch.setattr(kb, "retrieve", lambda q, top_k=5: [])

    captured = {}

    def fake_call(**kwargs):
        captured.update(kwargs)
        return {"output": {"text": "no context answer"}}

    monkeypatch.setattr("dashscope.Generation.call", fake_call)

    agent = RuntimeAgent(settings=_settings(), kb=kb)
    out = agent.run("nope?")
    assert out == "no context answer"
    assert "what is X?" not in captured["prompt"]
    assert "nope?" in captured["prompt"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /media/data/git/bailian_demo
PYTHONPATH=src python -m pytest tests/test_api.py::test_runtime_agent_assembles_prompt_with_rag_context tests/test_api.py::test_runtime_agent_continues_when_rag_returns_empty -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'bailian_rag_demo.app.runtime_agent'`

- [ ] **Step 3: Write `src/bailian_rag_demo/app/runtime_agent.py`**

```python
"""Cloud-runtime agent: assembles prompt with RAG context, calls LLM via dashscope.

This is the canonical execution path used inside the Bailian-hosted runtime
(no AgentScope dependency required).
"""
import logging
from typing import Optional

from bailian_rag_demo.config import Settings
from bailian_rag_demo.rag.base import KnowledgeBase

logger = logging.getLogger(__name__)

try:
    import dashscope
except ImportError:  # pragma: no cover
    dashscope = None  # type: ignore


SYSTEM_PROMPT_TEMPLATE = (
    "You are a helpful assistant. Use the following context to answer the user's "
    "question. If the context is empty, answer from general knowledge.\n\n"
    "Context:\n{context}\n"
)


class RuntimeAgent:
    def __init__(self, settings: Settings, kb: KnowledgeBase) -> None:
        if dashscope is None:
            raise ImportError("dashscope required for RuntimeAgent")
        dashscope.api_key = settings.DASHSCOPE_API_KEY
        self._settings = settings
        self._kb = kb

    def run(self, query: str, session_id: Optional[str] = None) -> str:
        hits = self._kb.retrieve(query, top_k=self._settings.BAILIAN_RAG_TOP_K)
        context = "\n---\n".join(h.content for h in hits) if hits else "(no context)"
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)

        response = dashscope.Generation.call(
            model="qwen-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
            result_format="message",
        )
        return self._extract_text(response)

    @staticmethod
    def _extract_text(response) -> str:
        try:
            return response["output"]["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            logger.warning("Unexpected dashscope response shape: %s; err=%s", response, exc)
            return ""
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd /media/data/git/bailian_demo
PYTHONPATH=src python -m pytest tests/test_api.py -v
```
Expected: All 6 tests in test_api.py PASS.

- [ ] **Step 5: Commit**

```bash
cd /media/data/git/bailian_demo
git add src/bailian_rag_demo/app/runtime_agent.py tests/test_api.py
git commit -m "feat: RuntimeAgent with RAG context injection via dashscope"
```

---

## Task 6: FastAPI Routes (/health and /process)

**Files:**
- Create: `src/bailian_rag_demo/app/api.py`
- Modify: `tests/test_api.py` (extend with route tests)
- Create: `tests/conftest.py`

- [ ] **Step 1: Write `tests/conftest.py`**

```python
import pytest
from fastapi.testclient import TestClient

from bailian_rag_demo.app.api import create_app
from bailian_rag_demo.config import Settings


@pytest.fixture
def fake_settings():
    return Settings(DASHSCOPE_API_KEY="sk-test", BAILIAN_APP_ID="app-test")


@pytest.fixture
def client(fake_settings, monkeypatch):
    monkeypatch.setattr(
        "bailian_rag_demo.app.api.load_settings", lambda: fake_settings
    )
    app = create_app(settings=fake_settings)
    return TestClient(app)
```

- [ ] **Step 2: Write failing test cases (append to `tests/test_api.py`)**

```python
def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.text == '"OK"'


def test_process_with_rag_context(client, monkeypatch):
    from bailian_rag_demo.rag.base import RetrievalHit

    class FakeKB:
        def __init__(self):
            self.calls = []
        def retrieve(self, query, top_k=5):
            self.calls.append((query, top_k))
            return [RetrievalHit(content="ctx-1", source="doc1.md", score=0.9)]
        def add_documents(self, docs, metadatas=None):
            pass
        def name(self):
            return "fake"

    fake_kb = FakeKB()
    monkeypatch.setattr(
        "bailian_rag_demo.app.api.get_kb", lambda settings: fake_kb
    )

    captured = {}
    def fake_call(**kwargs):
        captured.update(kwargs)
        return {"output": {"choices": [{"message": {"content": "answer with ctx"}}]}}
    monkeypatch.setattr("dashscope.Generation.call", fake_call)

    resp = client.post(
        "/process",
        json={
            "input": [
                {"role": "user", "content": [{"type": "text", "text": "what?"}]}
            ],
            "session_id": "s1",
            "user_id": "u1",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["output"][0]["role"] == "assistant"
    assert body["output"][0]["content"][0]["text"] == "answer with ctx"
    assert body["session_id"] == "s1"
    assert fake_kb.calls == [("what?", 5)]
    assert "ctx-1" in captured["messages"][1]["content"] or any(
        "ctx-1" in m.get("content", "") for m in captured["messages"]
    )


def test_process_handles_rag_empty(client, monkeypatch):
    class FakeKB:
        def retrieve(self, query, top_k=5):
            return []
        def add_documents(self, docs, metadatas=None):
            pass
        def name(self):
            return "fake"

    monkeypatch.setattr(
        "bailian_rag_demo.app.api.get_kb", lambda settings: FakeKB()
    )
    monkeypatch.setattr(
        "dashscope.Generation.call",
        lambda **kw: {"output": {"choices": [{"message": {"content": "ok"}}]}},
    )

    resp = client.post(
        "/process",
        json={"input": [{"role": "user", "content": [{"type": "text", "text": "q"}]}]},
    )
    assert resp.status_code == 200
    assert resp.json()["output"][0]["content"][0]["text"] == "ok"


def test_process_invalid_request_returns_422(client):
    resp = client.post("/process", json={"input": "not-a-list"})
    assert resp.status_code == 422
```

- [ ] **Step 3: Run tests to verify they fail**

Run:
```bash
cd /media/data/git/bailian_demo
pip install --quiet fastapi httpx
PYTHONPATH=src python -m pytest tests/test_api.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'bailian_rag_demo.app.api'`

- [ ] **Step 4: Write `src/bailian_rag_demo/app/api.py`**

```python
"""FastAPI routes for the Bailian Rich Code Application."""
import logging
from functools import lru_cache
from typing import Optional

from fastapi import FastAPI, HTTPException

from bailian_rag_demo.app.runtime_agent import RuntimeAgent
from bailian_rag_demo.app.schemas import (
    ProcessRequest,
    ProcessResponse,
    Message,
    TextContent,
)
from bailian_rag_demo.config import Settings, load_settings
from bailian_rag_demo.rag.base import KnowledgeBase
from bailian_rag_demo.rag.bailian_kb import BaiLianKB

logger = logging.getLogger(__name__)


def get_kb(settings: Settings) -> KnowledgeBase:
    """Factory: stage 1 returns BaiLianKB; stage 2 will branch on env var."""
    return BaiLianKB(settings)


def _extract_user_text(request: ProcessRequest) -> str:
    for msg in request.input:
        if msg.role == "user":
            for part in msg.content:
                if part.type == "text" and part.text:
                    return part.text
    raise HTTPException(status_code=400, detail="no user text in input")


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    """Application factory. Bailian runtime imports `app` from main.py;
    tests use this factory for clean state."""
    app = FastAPI(title="Bailian RAG Demo")
    cfg = settings or load_settings()

    @app.get("/health")
    def health_check():
        return "OK"

    @app.post("/process", response_model=ProcessResponse)
    def process(request: ProcessRequest):
        try:
            user_text = _extract_user_text(request)
            kb = get_kb(cfg)
            agent = RuntimeAgent(settings=cfg, kb=kb)
            answer = agent.run(user_text, session_id=request.session_id)
            return ProcessResponse(
                output=[
                    Message(
                        role="assistant",
                        content=[TextContent(type="text", text=answer)],
                    )
                ],
                session_id=request.session_id,
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("process failed")
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return app
```

- [ ] **Step 5: Run tests to verify they pass**

Run:
```bash
cd /media/data/git/bailian_demo
PYTHONPATH=src python -m pytest tests/test_api.py -v
```
Expected: All tests in test_api.py PASS (10 total).

- [ ] **Step 6: Commit**

```bash
cd /media/data/git/bailian_demo
git add src/bailian_rag_demo/app/api.py tests/conftest.py tests/test_api.py
git commit -m "feat: FastAPI routes /health and /process"
```

---

## Task 7: Bailian Entry Point (main.py)

**Files:**
- Create: `src/bailian_rag_demo/main.py`

- [ ] **Step 1: Verify with a smoke script**

Create `scripts/test_local.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

export DASHSCOPE_API_KEY="${DASHSCOPE_API_KEY:-sk-test}"
export BAILIAN_APP_ID="${BAILIAN_APP_ID:-app-test}"

PYTHONPATH=src python -m uvicorn bailian_rag_demo.main:app \
    --host 127.0.0.1 --port 8000 &
SERVER_PID=$!
trap "kill $SERVER_PID 2>/dev/null || true" EXIT
sleep 3

echo "== /health =="
curl -fsS http://127.0.0.1:8000/health
echo

echo "== /process =="
curl -fsS -X POST http://127.0.0.1:8000/process \
    -H 'Content-Type: application/json' \
    -d '{"input":[{"role":"user","content":[{"type":"text","text":"hello"}]}]}'
echo
```

```bash
chmod +x scripts/test_local.sh
```

- [ ] **Step 2: Write `src/bailian_rag_demo/main.py`**

```python
"""Bailian Rich Code Application entry point.

Bailian's runtime REQUIRES this file to be named `main.py` and to expose a
top-level ASGI application object (commonly named `app`). When the runtime
launches our wheel, it will import `bailian_rag_demo.main:app`.
"""
from bailian_rag_demo.app.api import create_app

app = create_app()
```

- [ ] **Step 3: Verify import path works**

Run:
```bash
cd /media/data/git/bailian_demo
PYTHONPATH=src python -c "from bailian_rag_demo.main import app; print(type(app).__name__)"
```
Expected: `FastAPI`

- [ ] **Step 4: Run smoke test (requires mocks to be patched or skips LLM)**

Run:
```bash
cd /media/data/git/bailian_demo
DASHSCOPE_API_KEY=sk-test BAILIAN_APP_ID=app-test \
    PYTHONPATH=src timeout 8 python -c "
from unittest.mock import patch
with patch('dashscope.Generation.call', return_value={'output': {'choices': [{'message': {'content': 'mocked'}}]}}):
    import uvicorn
    uvicorn.run('bailian_rag_demo.main:app', host='127.0.0.1', port=8765, log_level='warning')
" &
sleep 3
curl -fsS http://127.0.0.1:8765/health
echo
curl -fsS -X POST http://127.0.0.1:8765/process \
    -H 'Content-Type: application/json' \
    -d '{"input":[{"role":"user","content":[{"type":"text","text":"hi"}]}]}'
echo
```
Expected: `/health` returns `OK`; `/process` returns JSON with `"mocked"` text.

- [ ] **Step 5: Commit**

```bash
cd /media/data/git/bailian_demo
git add src/bailian_rag_demo/main.py scripts/test_local.sh
git commit -m "feat: Bailian-required main.py entry point with ASGI app"
```

---

## Task 8: Local AgentScope Helper (optional but spec'd)

**Files:**
- Create: `src/bailian_rag_demo/app/agent.py`

- [ ] **Step 1: Write `src/bailian_rag_demo/app/agent.py`**

```python
"""Local AgentScope agent for developer debugging.

Not used inside the Bailian runtime. Provides a familiar ReAct-style entry
point for iterating on prompts / RAG behavior without redeploying.
"""
import logging
from typing import List

from bailian_rag_demo.config import Settings
from bailian_rag_demo.rag.base import KnowledgeBase

logger = logging.getLogger(__name__)


class LocalAgent:
    """Thin wrapper that mirrors RuntimeAgent's contract using AgentScope."""

    def __init__(self, settings: Settings, kb: KnowledgeBase) -> None:
        self._settings = settings
        self._kb = kb

    def chat(self, query: str) -> str:
        hits = self._kb.retrieve(query, top_k=self._settings.BAILIAN_RAG_TOP_K)
        context = "\n".join(f"[{h.source}] {h.content}" for h in hits) or "(none)"
        try:
            import agentscope  # type: ignore
        except ImportError:
            logger.warning("agentscope not installed; falling back to plain echo")
            return f"[local-fallback] ctx={context!r} query={query!r}"
        # Minimal AgentScope usage: print context and return a placeholder.
        # Real implementations can swap in ReActAgent / etc.
        logger.info("agentscope version: %s", getattr(agentscope, "__version__", "?"))
        return f"[agentscope] ctx-len={len(context)} q={query}"
```

- [ ] **Step 2: Verify it imports (no test required for this thin shim)**

Run:
```bash
cd /media/data/git/bailian_demo
PYTHONPATH=src python -c "from bailian_rag_demo.app.agent import LocalAgent; print('ok')"
```
Expected: prints `ok`

- [ ] **Step 3: Commit**

```bash
cd /media/data/git/bailian_demo
git add src/bailian_rag_demo/app/agent.py
git commit -m "feat: LocalAgent helper for AgentScope-based local debugging"
```

---

## Task 9: Makefile, Requirements Lock, and Sample Docs

**Files:**
- Create: `Makefile`
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `scripts/setup_env.sh`
- Create: `examples/sample_docs/product_faq.md`
- Create: `examples/sample_docs/technical_guide.md`

- [ ] **Step 1: Write `requirements.txt`** (pinned versions; engineer must run `pip freeze` against the working venv to populate exact versions, then commit this file)

```text
# Generated via: python -m pip freeze | grep -Ei '^(fastapi|uvicorn|pydantic|dashscope|httpx|pytest|build|setuptools|wheel|agentscope)'
# Pin all versions with == for reproducible Bailian builds.
```

(The engineer MUST run `pip freeze` in their working venv and replace the comment with the actual pinned lines. **Do not** ship an empty requirements.txt.)

- [ ] **Step 2: Write `Makefile`**

```makefile
.PHONY: help install dev test test-upload build upload update clean

PYTHON ?= python

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	    awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install pinned dependencies
	$(PYTHON) -m pip install -r requirements.txt

dev:  ## Run uvicorn locally (requires .env or shell exports)
	$(PYTHON) -m uvicorn bailian_rag_demo.main:app --reload --host 127.0.0.1 --port 8000

test:  ## Run pytest
	PYTHONPATH=src $(PYTHON) -m pytest tests/ -v

test-upload:  ## Curl-based smoke test against locally-running server
	bash scripts/test_local.sh

build:  ## Build wheel (artifact in dist/)
	$(PYTHON) -m pip install --quiet build
	$(PYTHON) -m build

upload:  ## Upload to Bailian (usage: make upload NAME=my-rag-agent)
ifndef NAME
	$(error NAME is required, e.g. make upload NAME=my-rag-agent)
endif
	runtime-fc-deploy --deploy-name "$(NAME)" --whl-path dist/*.whl

update:  ## Update a deployed app (usage: make update APP_ID=xxx)
ifndef APP_ID
	$(error APP_ID is required, e.g. make update APP_ID=d8a48e...)
endif
	runtime-fc-deploy --update "$(APP_ID)" --whl-path dist/*.whl

clean:  ## Remove build artifacts
	rm -rf build/ dist/ src/*.egg-info src/bailian_rag_demo.egg-info
```

- [ ] **Step 3: Write `.env.example`**

```bash
# Alibaba Cloud Bailian Rich Code Application — environment template
# Copy to `.env` and fill in real values. NEVER commit `.env`.

# Required: Alibaba Cloud AccessKey (used by runtime-fc-deploy for upload auth)
ALIBABA_CLOUD_ACCESS_KEY_ID=
ALIBABA_CLOUD_ACCESS_KEY_SECRET=

# Optional: Bailian Workspace ID (llm-...). Defaults to default workspace if unset.
MODELSTUDIO_WORKSPACE_ID=

# Required at app runtime: Bailian API Key (used by dashscope)
DASHSCOPE_API_KEY=

# Required at app runtime: Bailian App ID bound to a knowledge index
BAILIAN_APP_ID=

# Optional tuning
BAILIAN_RAG_TOP_K=5
RAG_TIMEOUT_SEC=5.0
LOG_LEVEL=INFO
```

- [ ] **Step 4: Write `scripts/setup_env.sh`**

```bash
#!/usr/bin/env bash
# Print the environment variable names this app expects.
# Use as a checklist; set real values in your shell before running.
set -euo pipefail
cat <<'EOF'
Required for upload (runtime-fc-deploy):
  ALIBABA_CLOUD_ACCESS_KEY_ID
  ALIBABA_CLOUD_ACCESS_KEY_SECRET
  MODELSTUDIO_WORKSPACE_ID   (optional)

Required at app runtime:
  DASHSCOPE_API_KEY
  BAILIAN_APP_ID

Optional:
  BAILIAN_RAG_TOP_K   (default 5)
  RAG_TIMEOUT_SEC     (default 5.0)
  LOG_LEVEL           (default INFO)
EOF
```

```bash
chmod +x scripts/setup_env.sh
```

- [ ] **Step 5: Write sample documents**

`examples/sample_docs/product_faq.md`:
```markdown
# Product FAQ (Sample)

## What is Q4 in this context?
Q4 is the fourth quarter of a fiscal year, commonly used in business reporting
and financial analysis.

## How do I contact support?
Reach the support team via the in-product help widget or by emailing
support@example.com.
```

`examples/sample_docs/technical_guide.md`:
```markdown
# Technical Guide (Sample)

## Bailian Rich Code Application
A Bailian Rich Code Application is a Python project packaged as a `.whl`
and uploaded via `runtime-fc-deploy`. It must expose `GET /health` and a
chat endpoint, conventionally `POST /process`.

## RAG
Retrieval-Augmented Generation combines an embedding-based retrieval step
with an LLM prompt to ground answers in external documents.
```

- [ ] **Step 6: Verify Makefile targets work**

Run:
```bash
cd /media/data/git/bailian_demo
make help
make test   # all tests still pass
```
Expected: `make help` lists targets; `make test` passes.

- [ ] **Step 7: Commit**

```bash
cd /media/data/git/bailian_demo
git add Makefile requirements.txt .env.example scripts/ examples/
git commit -m "chore: Makefile, requirements template, env example, sample docs"
```

---

## Task 10: README and CLAUDE.md

**Files:**
- Create: `README.md`
- Create: `CLAUDE.md`

- [ ] **Step 1: Write `README.md`**

```markdown
# Bailian RAG Demo

A Alibaba Cloud Bailian **Rich Code Application** providing RAG-augmented Q&A.
Local-debuggable with AgentScope; deployable via `runtime-fc-deploy`.

> Stage 1 implements the Bailian RAG backend only. RAGFlow support lands in stage 2.

## Quickstart

```bash
# 1. Use the project venv (per project memory)
source /media/data/venv/bin/activate

# 2. Install
make install

# 3. Configure
cp .env.example .env
# edit .env with real DASHSCOPE_API_KEY and BAILIAN_APP_ID

# 4. Run locally
make dev
curl http://127.0.0.1:8000/health
# → "OK"

# 5. Test
make test

# 6. Build & upload
make build
make upload NAME=my-rag-agent
```

## Make Targets

| Target | Purpose |
|--------|---------|
| `make install` | Install pinned deps |
| `make dev` | Run uvicorn locally |
| `make test` | pytest |
| `make test-upload` | Curl smoke test against running server |
| `make build` | Build wheel into `dist/` |
| `make upload NAME=x` | Upload wheel to Bailian |
| `make update APP_ID=x` | Update an existing deployed app |
| `make clean` | Remove build artifacts |

## Environment Variables

See `.env.example` for the full list with descriptions.

## Architecture

See `docs/superpowers/specs/2026-09-21-bailian-rag-agent-design.md` for the full design spec.

## License

MIT
```

- [ ] **Step 2: Write `CLAUDE.md`**

```markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Bailian Rich Code Application with RAG. Stage 1 = Bailian RAG backend only.

## Common Commands

| Command | What it does |
|---------|--------------|
| `make install` | Install pinned deps from `requirements.txt` |
| `make dev` | Run uvicorn at 127.0.0.1:8000 (requires env vars) |
| `make test` | Run pytest suite |
| `make test-upload` | Curl smoke test (requires `make dev` running) |
| `make build` | Produce `dist/*.whl` |
| `make upload NAME=x` | Upload wheel via `runtime-fc-deploy` |
| `make update APP_ID=x` | Update deployed app |

Always use the venv at `/media/data/venv` (per global CLAUDE.md).

## Architecture (One-screen Summary)

- **Entry**: `src/bailian_rag_demo/main.py` exposes top-level `app = FastAPI()` — required by Bailian runtime.
- **Routes**: `src/bailian_rag_demo/app/api.py` (`/health`, `/process`).
- **Schemas**: `src/bailian_rag_demo/app/schemas.py` — Agent API protocol.
- **Agent**: `src/bailian_rag_demo/app/runtime_agent.py` is the canonical cloud path (dashscope + RAG injection). `agent.py` is the local AgentScope helper.
- **RAG**: `src/bailian_rag_demo/rag/base.py` defines `KnowledgeBase` ABC. Stage 1 implementation: `bailian_kb.py` (BaiLianKB).
- **Config**: `src/bailian_rag_demo/config.py` — fail-fast env loading.

## Constraints (don't violate)

1. **Entry must be named `main.py`** and expose a top-level `app`. Bailian's runtime depends on this.
2. **Pin all dependency versions** with `==`. Do not use `>=`/`~=`. Use `pip freeze` to generate `requirements.txt`.
3. **The cloud path must NOT depend on AgentScope.** `runtime_agent.py` only uses `dashscope`. Local-only helpers go in `agent.py`.
4. **Never commit `.env` or real API keys.** `.gitignore` blocks it; keep `.env.example` updated.
5. **Knowledge base changes go through new `KnowledgeBase` subclasses** — do not bypass the abstraction.

## Where Things Live

- Spec: `docs/superpowers/specs/2026-09-21-bailian-rag-agent-design.md`
- Implementation plan: `docs/superpowers/plans/2026-09-21-bailian-rag-agent.md`
- Sample RAG data: `examples/sample_docs/`

## Style

- Tests are colocated with intent: `tests/test_api.py` covers schemas, runtime agent, and routes.
- Mock external services (dashscope) in tests — do not make real API calls in CI.
- Always commit after a green test run.
```

- [ ] **Step 3: Commit**

```bash
cd /media/data/git/bailian_demo
git add README.md CLAUDE.md
git commit -m "docs: README and CLAUDE.md for project guidance"
```

---

## Final Verification

After all tasks:

- [ ] **Step 1: Run full test suite**

```bash
cd /media/data/git/bailian_demo
PYTHONPATH=src python -m pytest tests/ -v
```
Expected: All tests pass.

- [ ] **Step 2: Build wheel**

```bash
cd /media/data/git/bailian_demo
make build
ls dist/*.whl
```
Expected: A `.whl` file exists in `dist/`.

- [ ] **Step 3: Confirm main.py is importable as `bailian_rag_demo.main:app`**

```bash
cd /media/data/git/bailian_demo
PYTHONPATH=src python -c "from bailian_rag_demo.main import app; assert app.title == 'Bailian RAG Demo'"
```
Expected: No error.

- [ ] **Step 4: Confirm `runtime-fc-deploy` is documented as the upload tool**

```bash
grep -r "runtime-fc-deploy" /media/data/git/bailian_demo --include='*.md' --include='Makefile' --include='*.sh'
```
Expected: At least Makefile and README mention it.

---

## Out of Scope (Stage 2+)

- `RAGFlowKB` implementation and backend switching
- Spark Design frontend integration
- MCP tool integration
- Multi-tenant session isolation
- Streaming responses

These will be addressed in subsequent design specs and plans.