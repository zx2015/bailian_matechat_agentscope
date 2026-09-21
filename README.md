# Bailian RAG Demo

A Alibaba Cloud Bailian **Rich Code Application** providing RAG-augmented Q&A,
with a [MateChat](https://matechat.gitcode.com/) chat UI and an
[AgentScope](https://github.com/agentscope-ai/agentscope) `ReActAgent` running
**both locally and inside the Bailian-hosted runtime** — the same agent stack
everywhere, only the deployment target differs. Deployable via `runtime-fc-deploy`.

> Stage 1 implements the Bailian RAG backend only. RAGFlow support lands in stage 2.

## Architecture at a Glance

```
MateChat (Vue, frontend/) ──POST /process──▶ FastAPI (main.py)
                                                  │
                                          RuntimeAgent (AgentScope ReActAgent)
                                                  │
                            BaiLianKB.retrieve() ──▶ 百炼知识库 Retrieve OpenAPI (AK/SK)
                                                  │
                                    DashScopeChatModel ──▶ 百炼 LLM (dashscope)
```

- The FastAPI backend serves the built MateChat frontend as static files at `/`,
  and exposes the Bailian-required `GET /health` and `POST /process` API.
- `RuntimeAgent` (`app/runtime_agent.py`) wraps an AgentScope `ReActAgent` bound
  to a `DashScopeChatModel`; it keeps one per-session agent instance so
  multi-turn conversations retain memory across `/process` calls.
- RAG retrieval stays behind the `KnowledgeBase` abstraction (`BaiLianKB`).
  As of stage 1.2, `BaiLianKB` calls the Bailian knowledge base `Retrieve`
  OpenAPI **directly** (via `alibabacloud_bailian20231229` + AccessKey auth),
  bypassing the Bailian "application" concept entirely — this avoids an
  entire class of silent failures where an application isn't actually bound
  to a knowledge base in the console. Retrieved context is folded into the
  user turn before AgentScope reasons over it.

## Quickstart

```bash
# 1. Use the project venv (per project memory)
source /media/data/venv/bin/activate

# 2. Install backend deps
make install

# 3. Configure
cp .env.example .env
# edit .env with real DASHSCOPE_API_KEY, ALIBABA_CLOUD_ACCESS_KEY_ID/SECRET,
# BAILIAN_WORKSPACE_ID, and BAILIAN_INDEX_ID

# 4. Build the MateChat frontend (requires Node.js + npm)
make frontend-build

# 5. Run locally
make dev
curl http://127.0.0.1:8000/health          # → "OK"
open http://127.0.0.1:8000/                # MateChat chat UI

# 6. Test
make test

# 7. Build & upload
make build
make upload NAME=my-rag-agent
```

For frontend-only iteration (hot reload, proxies `/process`+`/health` to
`127.0.0.1:8000`):

```bash
cd frontend && npm install && npm run dev
```

## Make Targets

| Target | Purpose |
|--------|---------|
| `make install` | Install pinned backend deps |
| `make frontend-install` | Install MateChat frontend npm deps |
| `make frontend-build` | Build MateChat frontend and copy it into `src/bailian_rag_demo/static/` |
| `make dev` | Run uvicorn locally |
| `make test` | pytest |
| `make test-upload` | Curl smoke test against running server |
| `make build` | Build wheel (runs `frontend-build` first, so the UI ships in `dist/*.whl`) |
| `make upload NAME=x` | Upload wheel to Bailian |
| `make update APP_ID=x` | Update an existing deployed app |
| `make clean` | Remove build artifacts (backend + frontend) |

## Deploying to Bailian

Uploading uses `runtime-fc-deploy` (a CLI from the `agentscope-runtime`
package — note: that repo is archived upstream in favor of AgentScope 2.0,
but the CLI script is still published and works).

```bash
# One-time: install the deploy tool + cloud SDKs it needs
pip install agentscope-runtime alibabacloud-oss-v2 alibabacloud-credentials alibabacloud-tea-util

# Deployment-only env vars (separate from the app's own runtime config above):
#   ALIBABA_CLOUD_ACCESS_KEY_ID / _SECRET  -- reused from your .env
#   MODELSTUDIO_WORKSPACE_ID               -- usually same value as BAILIAN_WORKSPACE_ID,
#                                              but a different tool reading a different env var name
export MODELSTUDIO_WORKSPACE_ID=<your-workspace-id>

make build                          # builds frontend + wheel (dist/*.whl)
make upload NAME=my-rag-agent       # uploads dist/*.whl, creates a new app
# ...or, to update an existing one:
make update APP_ID=<deploy-id-from-previous-upload>
```

A successful upload prints a `Deploy ID` and a console URL
(`https://bailian.console.aliyun.com/?tab=app#/app-center`). Check status
any time with `agentscope status <deploy-id>` or `agentscope list`.

**Important — the wheel's own metadata must declare its dependencies.**
`--whl-path` mode uploads *only* the wheel; there's no separate
`requirements.txt` upload step, so pip resolves dependencies purely from
the wheel's `Requires-Dist` metadata. That's why `pyproject.toml` declares
`[project.dependencies]` (direct deps, pinned) even though `requirements.txt`
(fully-pinned, transitive-inclusive) remains the source of truth for local
dev installs — keep both in sync when adding a new direct dependency.

**Important — environment variables for the deployed app.** `runtime-fc-deploy`
in `--whl-path` mode has no flag to pass the app's own runtime env vars
(`DASHSCOPE_API_KEY`, `ALIBABA_CLOUD_ACCESS_KEY_ID/SECRET`,
`BAILIAN_WORKSPACE_ID`, `BAILIAN_INDEX_ID`, etc.) — since `config.py` is
fail-fast, the app will crash on startup until these are configured in the
**Bailian console** for the deployed app (under its settings/环境变量 after
opening it from the app center URL above).

## Environment Variables

See `.env.example` for the full list with descriptions. To find your
`BAILIAN_WORKSPACE_ID` and `BAILIAN_INDEX_ID`:

```bash
# Install the Alibaba Cloud CLI, then list knowledge bases in your workspace:
aliyun configure --profile bailian set --access-key-id <AK> --access-key-secret <SK> --region cn-beijing
aliyun bailian ListIndices --WorkspaceId <your-workspace-id>
```

`WorkspaceId` itself can only be found in the console (there is no API for
it) — see [obtaining APP ID and Workspace ID](https://help.aliyun.com/zh/model-studio/obtain-the-app-id-and-workspace-id).

**Known limitation**: knowledge base documents parsed with the `DOCMIND`
parser (Bailian's default for scanned/complex PDFs) are chunked as
image-based nodes with **empty text** (only an `image_url`), so they can't
be used for this project's text-only RAG flow. `BaiLianKB` filters these out
automatically and falls back to the LLM's general knowledge. For a knowledge
base that reliably returns real text context, upload plain-text/Markdown/
digital-native documents (parsed with `DOCMIND_DIGITAL`) — see
`examples/sample_docs/`.

## Architecture

See `docs/superpowers/specs/2026-09-21-bailian-rag-agent-design.md` for the full design spec
(includes the stage 1.1 MateChat + AgentScope update, stage 1.2 direct-Retrieve-API update,
and the stage 1.3 deployment notes).

## License

MIT
