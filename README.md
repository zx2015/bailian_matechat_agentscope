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
(includes the stage 1.1 MateChat + AgentScope update and the stage 1.2 direct-Retrieve-API update).

## License

MIT
