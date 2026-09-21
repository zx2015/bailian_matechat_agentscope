from unittest.mock import patch, MagicMock
import pytest

from bailian_rag_demo.rag.base import RetrievalHit
from bailian_rag_demo.rag.bailian_kb import BaiLianKB


def _settings(top_k=5, timeout=5.0):
    from bailian_rag_demo.config import Settings
    return Settings(
        DASHSCOPE_API_KEY="sk-test",
        BAILIAN_APP_ID="app-test",
        BAILIAN_RAG_TOP_K=top_k,
        RAG_TIMEOUT_SEC=timeout,
    )


def test_retrieval_hit_dataclass():
    hit = RetrievalHit(content="hi", source="doc.md", score=0.9)
    assert hit.content == "hi"
    assert hit.source == "doc.md"
    assert hit.score == 0.9


def test_bailian_kb_name():
    kb = BaiLianKB(_settings())
    assert kb.name() == "bailian"


def test_bailian_kb_retrieve_parses_dashscope_response():
    settings = _settings(top_k=3)
    kb = BaiLianKB(settings)

    mock_response = {
        "output": {
            "text": "answer",
            "doc_references": [
                {"title": "doc1.md", "content": "snippet 1", "score": 0.9},
                {"title": "doc2.md", "content": "snippet 2", "score": 0.8},
            ],
        }
    }

    with patch("bailian_rag_demo.rag.bailian_kb.dashscope") as mock_ds:
        mock_ds.Application.call.return_value = mock_response
        hits = kb.retrieve("what is X?", top_k=3)

    assert len(hits) == 2
    assert hits[0].content == "snippet 1"
    assert hits[0].source == "doc1.md"
    assert hits[0].score == 0.9
    assert hits[1].source == "doc2.md"

    call_kwargs = mock_ds.Application.call.call_args.kwargs
    assert call_kwargs["app_id"] == "app-test"
    assert call_kwargs["prompt"] == "what is X?"
    # `top_k` must NEVER be forwarded to Application.call: on the real
    # dashscope API it's an LLM sampling parameter (candidate set size),
    # not a "number of retrieved docs" knob, and passing it here would
    # silently corrupt generation behavior instead of controlling
    # retrieval scope. `doc_reference_type` is what actually requests
    # `doc_references` back from a RAG-bound Bailian app.
    assert "top_k" not in call_kwargs
    assert call_kwargs["doc_reference_type"] == "indexed"


def test_bailian_kb_retrieve_empty_when_no_references():
    settings = _settings()
    kb = BaiLianKB(settings)

    with patch("bailian_rag_demo.rag.bailian_kb.dashscope") as mock_ds:
        mock_ds.Application.call.return_value = {"output": {"text": "no refs"}}
        hits = kb.retrieve("nope")

    assert hits == []


def test_bailian_kb_retrieve_returns_empty_on_exception(caplog):
    settings = _settings()
    kb = BaiLianKB(settings)

    with patch("bailian_rag_demo.rag.bailian_kb.dashscope") as mock_ds:
        mock_ds.Application.call.side_effect = RuntimeError("network down")
        hits = kb.retrieve("query")

    assert hits == []


def test_bailian_kb_retrieve_timeout_returns_empty(caplog):
    import time
    settings = _settings(timeout=0.05)
    kb = BaiLianKB(settings)

    def slow_call(**kwargs):
        time.sleep(0.2)
        return {"output": {"text": "too slow"}}

    with patch("bailian_rag_demo.rag.bailian_kb.dashscope") as mock_ds:
        mock_ds.Application.call.side_effect = slow_call
        hits = kb.retrieve("query")

    assert hits == []
    assert any("timeout" in record.message.lower() for record in caplog.records)


def test_bailian_kb_add_documents_not_implemented():
    kb = BaiLianKB(_settings())
    with pytest.raises(NotImplementedError):
        kb.add_documents(["text"])