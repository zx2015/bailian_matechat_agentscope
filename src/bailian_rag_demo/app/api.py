"""FastAPI routes for the Bailian Rich Code Application."""
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

from bailian_rag_demo.app.runtime_agent import RuntimeAgent
from bailian_rag_demo.app.schemas import (
    ProcessRequest,
    ProcessResponse,
    Message,
    TextContent,
    Reference,
)
from bailian_rag_demo.config import Settings, load_settings
from bailian_rag_demo.rag.base import KnowledgeBase
from bailian_rag_demo.rag.bailian_kb import BaiLianKB

# Built by `make frontend-build` (MateChat + Vue), copied here so it ships
# inside the wheel. Optional: the API still works without it.
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

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
    # One RuntimeAgent per app instance: it keeps per-session AgentScope
    # conversation memory alive across `/process` calls.
    agent = RuntimeAgent(settings=cfg)

    @app.get("/health", response_class=PlainTextResponse)
    def health_check():
        return "OK"

    @app.post("/process", response_model=ProcessResponse)
    async def process(request: ProcessRequest):
        try:
            user_text = _extract_user_text(request)
            kb = get_kb(cfg)
            answer, usage, sources = await agent.run_async(
                user_text, kb, session_id=request.session_id
            )
            return ProcessResponse(
                output=[
                    Message(
                        role="assistant",
                        content=[TextContent(type="text", text=answer)],
                    )
                ],
                session_id=request.session_id,
                usage=usage,
                references=(
                    [Reference(source=h.source, score=h.score) for h in sources]
                    if sources
                    else None
                ),
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("process failed")
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Serve the MateChat frontend build (if present) at the root path. This
    # is a catch-all mount, so it must be registered after /health and
    # /process to avoid shadowing them.
    if STATIC_DIR.is_dir():
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="frontend")

    return app