import pytest
from bailian_rag_demo.app.schemas import (
    ProcessRequest,
    ProcessResponse,
    TextContent,
    Message,
)


def test_text_content_validation():
    tc = TextContent(type="text", text="hello")
    assert tc.text == "hello"
    assert tc.type == "text"


def test_message_validation():
    msg = Message(role="user", content=[TextContent(type="text", text="hi")])
    assert msg.role == "user"
    assert msg.content[0].text == "hi"


def test_process_request_minimum():
    req = ProcessRequest(
        input=[Message(role="user", content=[TextContent(type="text", text="q")])]
    )
    assert req.session_id is None
    assert req.user_id is None


def test_process_response_construction():
    resp = ProcessResponse(
        output=[Message(role="assistant", content=[TextContent(type="text", text="a")])],
        session_id="s1",
        usage={"input_tokens": 10, "output_tokens": 20},
    )
    assert resp.session_id == "s1"
    assert resp.usage["output_tokens"] == 20


from bailian_rag_demo.app.runtime_agent import RuntimeAgent
from bailian_rag_demo.rag.bailian_kb import BaiLianKB
from bailian_rag_demo.config import Settings


def _settings():
    return Settings(DASHSCOPE_API_KEY="sk-test", BAILIAN_APP_ID="app-test")


def test_runtime_agent_assembles_prompt_with_rag_context(monkeypatch):
    kb = BaiLianKB(_settings())
    # pre-seed with deterministic hits
    from bailian_rag_demo.rag.base import RetrievalHit
    monkeypatch.setattr(kb, "retrieve", lambda q, top_k=5: [
        RetrievalHit(content="ctx-1", source="doc1.md", score=0.9)
    ])

    captured = {}

    def fake_call(**kwargs):
        captured.update(kwargs)
        return {"output": {"text": "OK answer"}, "usage": {"input_tokens": 5, "output_tokens": 7}}

    monkeypatch.setattr("bailian_rag_demo.app.runtime_agent.dashscope", __import__("dashscope", fromlist=["*"]))
    monkeypatch.setattr("dashscope.Generation.call", fake_call)

    agent = RuntimeAgent(settings=_settings(), kb=kb)
    out = agent.run("what is X?", session_id="s1")

    assert out == "OK answer"
    assert "ctx-1" in captured["prompt"]
    assert "what is X?" in captured["prompt"]


def test_runtime_agent_continues_when_rag_returns_empty(monkeypatch):
    kb = BaiLianKB(_settings())
    monkeypatch.setattr(kb, "retrieve", lambda q, top_k=5: [])

    captured = {}

    def fake_call(**kwargs):
        captured.update(kwargs)
        return {"output": {"text": "no context answer"}}

    monkeypatch.setattr("dashscope.Generation.call", fake_call)

    agent = RuntimeAgent(settings=_settings(), kb=kb)
    out = agent.run("nope?")
    assert out == "no context answer"
    assert "what is X?" not in captured["prompt"]
    assert "nope?" in captured["prompt"]