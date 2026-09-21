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
