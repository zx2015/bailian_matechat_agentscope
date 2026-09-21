"""Bailian (Alibaba Cloud Model Studio) RAG backend.

Retrieves directly from a Bailian knowledge base index via the
`alibabacloud_bailian20231229` OpenAPI SDK (`Retrieve` action), instead of
going through `dashscope.Application.call()` on a Bailian "application".

Why: an Bailian *application* must be explicitly bound to a knowledge base
in the console for `Application.call()` to return `doc_references`; there is
no API to verify/set that binding, and a misconfigured app silently
degrades to zero-context RAG with no error. Calling `Retrieve` directly
against a known `(workspace_id, index_id)` is unambiguous and independently
verifiable (e.g. via `aliyun bailian ListIndices` / `Retrieve` CLI calls),
and doesn't depend on any application's console configuration at all.
"""
import concurrent.futures
import logging
from typing import List, Dict, Optional

from bailian_rag_demo.rag.base import KnowledgeBase, RetrievalHit
from bailian_rag_demo.config import Settings

logger = logging.getLogger(__name__)

try:
    from alibabacloud_tea_openapi import models as open_api_models
    from alibabacloud_bailian20231229.client import Client as BailianClient
    from alibabacloud_bailian20231229 import models as bailian_models
except ImportError:  # pragma: no cover
    open_api_models = None  # type: ignore
    BailianClient = None  # type: ignore
    bailian_models = None  # type: ignore


class BaiLianKB(KnowledgeBase):
    """RAG backend that retrieves directly from a Bailian knowledge base
    index (bypasses the "application" concept entirely)."""

    def __init__(self, settings: Settings) -> None:
        if BailianClient is None:
            raise ImportError(
                "alibabacloud_bailian20231229 is required for BaiLianKB; "
                "install via `pip install alibabacloud_bailian20231229`"
            )
        self._settings = settings
        config = open_api_models.Config(
            access_key_id=settings.ALIBABA_CLOUD_ACCESS_KEY_ID,
            access_key_secret=settings.ALIBABA_CLOUD_ACCESS_KEY_SECRET,
            endpoint=f"bailian.{settings.BAILIAN_REGION_ID}.aliyuncs.com",
        )
        self._client = BailianClient(config)

    def name(self) -> str:
        return "bailian"

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalHit]:
        timeout = self._settings.RAG_TIMEOUT_SEC
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                request = bailian_models.RetrieveRequest(
                    index_id=self._settings.BAILIAN_INDEX_ID,
                    query=query,
                    dense_similarity_top_k=top_k,
                )
                future = ex.submit(
                    self._client.retrieve,
                    workspace_id=self._settings.BAILIAN_WORKSPACE_ID,
                    request=request,
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
                    "BaiLianKB.retrieve returned no usable text chunks for "
                    "index_id=%s workspace_id=%s; check that the index has "
                    "indexed documents with extractable text (scanned/"
                    "image-parsed PDFs using the DOCMIND parser return "
                    "chunks with empty text, only image_url).",
                    self._settings.BAILIAN_INDEX_ID,
                    self._settings.BAILIAN_WORKSPACE_ID,
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
    def _parse_response(response) -> List[RetrievalHit]:
        body = getattr(response, "body", None)
        data = getattr(body, "data", None)
        nodes = getattr(data, "nodes", None) or []
        hits: List[RetrievalHit] = []
        for node in nodes:
            text = getattr(node, "text", None)
            if not text:
                # Nodes from image-parsed (DOCMIND) documents have no text
                # content -- skip them rather than injecting an empty
                # context block into the LLM prompt.
                continue
            metadata = getattr(node, "metadata", None) or {}
            source = (
                metadata.get("doc_name")
                if isinstance(metadata, dict)
                else getattr(metadata, "doc_name", None)
            ) or "unknown"
            hits.append(
                RetrievalHit(
                    content=text,
                    source=source,
                    score=float(getattr(node, "score", 0.0) or 0.0),
                )
            )
        return hits
