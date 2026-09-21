from types import SimpleNamespace
from unittest.mock import patch
import pytest

from bailian_rag_demo.rag.base import RetrievalHit
from bailian_rag_demo.rag.bailian_kb import BaiLianKB
from bailian_rag_demo.config import Settings


def _settings(top_k=5, timeout=10.0):
    return Settings(
        DASHSCOPE_API_KEY="sk-test",
        ALIBABA_CLOUD_ACCESS_KEY_ID="ak-test",
        ALIBABA_CLOUD_ACCESS_KEY_SECRET="ak-secret-test",
        BAILIAN_WORKSPACE_ID="ws-test",
        BAILIAN_INDEX_ID="idx-test",
        BAILIAN_RAG_TOP_K=top_k,
        RAG_TIMEOUT_SEC=timeout,
    )


def _fake_node(text, score, doc_name):
    return SimpleNamespace(text=text, score=score, metadata={"doc_name": doc_name})


def _fake_response(nodes):
    return SimpleNamespace(body=SimpleNamespace(data=SimpleNamespace(nodes=nodes)))


def test_retrieval_hit_dataclass():
    hit = RetrievalHit(content="hi", source="doc.md", score=0.9)
    assert hit.content == "hi"
    assert hit.source == "doc.md"
    assert hit.score == 0.9


def test_bailian_kb_name():
    with patch("bailian_rag_demo.rag.bailian_kb.BailianClient"):
        kb = BaiLianKB(_settings())
    assert kb.name() == "bailian"


def test_bailian_kb_retrieve_parses_response():
    with patch("bailian_rag_demo.rag.bailian_kb.BailianClient") as MockClient:
        instance = MockClient.return_value
        instance.retrieve.return_value = _fake_response(
            [
                _fake_node("snippet 1", 0.9, "doc1.pdf"),
                _fake_node("snippet 2", 0.8, "doc2.pdf"),
            ]
        )
        kb = BaiLianKB(_settings(top_k=3))
        hits = kb.retrieve("what is X?", top_k=3)

    assert len(hits) == 2
    assert hits[0].content == "snippet 1"
    assert hits[0].source == "doc1.pdf"
    assert hits[0].score == 0.9
    assert hits[1].source == "doc2.pdf"

    call_kwargs = instance.retrieve.call_args.kwargs
    assert call_kwargs["workspace_id"] == "ws-test"
    request = call_kwargs["request"]
    assert request.index_id == "idx-test"
    assert request.query == "what is X?"
    assert request.dense_similarity_top_k == 3


def test_bailian_kb_retrieve_skips_empty_text_nodes():
    """Chunks from image-parsed (DOCMIND) documents have empty/None text
    (only an image_url); they must be filtered out rather than injected as
    blank context into the LLM prompt."""
    with patch("bailian_rag_demo.rag.bailian_kb.BailianClient") as MockClient:
        instance = MockClient.return_value
        instance.retrieve.return_value = _fake_response(
            [
                _fake_node("", 0.9, "scanned.pdf"),
                _fake_node(None, 0.8, "scanned2.pdf"),
            ]
        )
        kb = BaiLianKB(_settings())
        hits = kb.retrieve("query")

    assert hits == []


def test_bailian_kb_retrieve_returns_empty_on_exception():
    with patch("bailian_rag_demo.rag.bailian_kb.BailianClient") as MockClient:
        instance = MockClient.return_value
        instance.retrieve.side_effect = RuntimeError("network down")
        kb = BaiLianKB(_settings())
        hits = kb.retrieve("query")

    assert hits == []


def test_bailian_kb_retrieve_timeout_returns_empty(caplog):
    import time

    with patch("bailian_rag_demo.rag.bailian_kb.BailianClient") as MockClient:
        instance = MockClient.return_value

        def slow_call(**kwargs):
            time.sleep(0.2)
            return _fake_response([])

        instance.retrieve.side_effect = slow_call
        kb = BaiLianKB(_settings(timeout=0.05))
        with caplog.at_level("WARNING"):
            hits = kb.retrieve("query")

    assert hits == []
    assert any("timeout" in record.message.lower() for record in caplog.records)


def test_bailian_kb_add_documents_not_implemented():
    with patch("bailian_rag_demo.rag.bailian_kb.BailianClient"):
        kb = BaiLianKB(_settings())
    with pytest.raises(NotImplementedError):
        kb.add_documents(["text"])
