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