# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Bailian Rich Code Application with RAG + MateChat frontend. Stage 1 = Bailian RAG backend + MateChat UI + AgentScope agent (both local and cloud runtime).

## Common Commands

| Command | What it does |
|---------|--------------|
| `make install` | Install pinned backend deps from `requirements.txt` |
| `make frontend-install` | Install MateChat frontend npm deps (`frontend/`) |
| `make frontend-build` | Build MateChat frontend, copy into `src/bailian_rag_demo/static/` |
| `make dev` | Run uvicorn at 127.0.0.1:8000 (requires env vars); serves API + built frontend |
| `make test` | Run pytest suite |
| `make test-upload` | Curl smoke test (requires `make dev` running) |
| `make build` | Build frontend then produce `dist/*.whl` (frontend bundled inside) |
| `make upload NAME=x` | Upload wheel via `runtime-fc-deploy` |
| `make update APP_ID=x` | Update deployed app |

Always use the venv at `/media/data/venv` (per global CLAUDE.md).

## Architecture (One-screen Summary)

- **Entry**: `src/bailian_rag_demo/main.py` exposes top-level `app = FastAPI()` — required by Bailian runtime.
- **Routes**: `src/bailian_rag_demo/app/api.py` (`/health`, `/process`, static-mounted MateChat build at `/`).
- **Schemas**: `src/bailian_rag_demo/app/schemas.py` — Agent API protocol.
- **Agent**: `src/bailian_rag_demo/app/runtime_agent.py::RuntimeAgent` wraps an AgentScope `ReActAgent` bound to a `DashScopeChatModel`. This is the **single** agent implementation used both locally and inside the Bailian-hosted runtime (one `ReActAgent` instance kept per `session_id` for multi-turn memory). `app/agent.py` is a thin stdin/stdout debug loop around the same `RuntimeAgent`.
- **RAG**: `src/bailian_rag_demo/rag/base.py` defines `KnowledgeBase` ABC. Stage 1 implementation: `bailian_kb.py` (BaiLianKB). As of stage 1.2, `BaiLianKB` calls the Bailian knowledge base `Retrieve` OpenAPI **directly** via `alibabacloud_bailian20231229` (AccessKey auth: `ALIBABA_CLOUD_ACCESS_KEY_ID`/`_SECRET`, `BAILIAN_WORKSPACE_ID`, `BAILIAN_INDEX_ID`) — it no longer goes through `dashscope.Application.call()`/`BAILIAN_APP_ID` (deprecated, kept optional for backward compat only), since that required an "application" to be manually bound to a knowledge base in the console with no way to verify the binding via API. Nodes with empty `text` (image-parsed/`DOCMIND` documents) are filtered out. Retrieved chunks are folded into the user turn's content before being handed to AgentScope; RAG stays swappable without touching agent orchestration.
- **Config**: `src/bailian_rag_demo/config.py` — fail-fast env loading.
- **Frontend**: `frontend/` — Vue 3 + [MateChat](https://matechat.gitcode.com/) chat UI. `npm run build` output is copied to `src/bailian_rag_demo/static/` and mounted by FastAPI at `/`, so it ships inside the wheel and is served by the same Bailian runtime process (no separate frontend deployment).

## Constraints (don't violate)

1. **Entry must be named `main.py`** and expose a top-level `app`. Bailian's runtime depends on this.
2. **Pin all dependency versions** with `==`. Do not use `>=`/`~=`. Use `pip freeze` (in a clean venv) to generate `requirements.txt`.
3. **`agentscope` is now a required runtime dependency** (not local-only). `RuntimeAgent` is the one agent implementation for both local dev and the Bailian runtime — do not fork it into separate cloud/local code paths.
4. **Never commit `.env` or real API keys.** `.gitignore` blocks it; keep `.env.example` updated.
5. **Knowledge base changes go through new `KnowledgeBase` subclasses** — do not bypass the abstraction.
6. **Frontend build artifacts (`frontend/dist/`, `src/bailian_rag_demo/static/`) are generated, not committed.** Always rebuild via `make frontend-build` before `make build`/`make dev` if you need the UI served.

## Where Things Live

- Spec: `docs/superpowers/specs/2026-09-21-bailian-rag-agent-design.md` (see the stage 1.1 addendum for the MateChat + AgentScope update)
- Implementation plan: `docs/superpowers/plans/2026-09-21-bailian-rag-agent.md`
- Sample RAG data: `examples/sample_docs/`
- Frontend source: `frontend/src/App.vue`, `frontend/src/main.ts`

## Style

- Tests are colocated with intent: `tests/test_api.py` covers schemas, runtime agent, and routes.
- Mock the AgentScope model layer (`DashScopeChatModel.__call__`) in tests — do not make real API calls in CI.
- Always commit after a green test run.
