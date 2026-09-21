"""Bailian (Alibaba Cloud Model Studio) RAG backend via dashscope."""
import concurrent.futures
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
        timeout = self._settings.RAG_TIMEOUT_SEC
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(
                    dashscope.Application.call,
                    app_id=self._settings.BAILIAN_APP_ID,
                    prompt=query,
                    # NOTE: dashscope.Application.call's `top_k` parameter
                    # controls LLM *sampling* (candidate set size), not the
                    # number of retrieved documents -- there is no
                    # client-side knob for retrieval count on this API; the
                    # Bailian app's bound knowledge base/pipeline config
                    # controls that server-side. Do NOT pass `top_k` here
                    # (it would silently change generation behavior).
                    # `doc_reference_type="indexed"` asks the API to return
                    # `doc_references` when the app has RAG configured.
                    doc_reference_type="indexed",
                )
                try:
                    response = future.result(timeout=timeout)
                except concurrent.futures.TimeoutError:
                    logger.warning(
                        "BaiLianKB.retrieve timeout after %ss", timeout
                    )
                    return []
            hits = self._parse_response(response)
            if not hits:
                logger.info(
                    "BaiLianKB.retrieve returned no doc_references for "
                    "app_id=%s; verify in the Bailian console that this "
                    "app is bound to a knowledge base with indexed "
                    "documents.",
                    self._settings.BAILIAN_APP_ID,
                )
            return hits
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