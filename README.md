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
