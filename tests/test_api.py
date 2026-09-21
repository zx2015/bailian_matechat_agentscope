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
    out, usage = agent.run("what is X?", session_id="s1")

    assert out == "OK answer"
    assert usage == {"input_tokens": 5, "output_tokens": 7}
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
    out, usage = agent.run("nope?")
    assert out == "no context answer"
    assert usage is None or usage == {}
    assert "what is X?" not in captured["prompt"]
    assert "nope?" in captured["prompt"]


def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.text == "OK"


def test_process_with_rag_context(client, monkeypatch):
    from bailian_rag_demo.rag.base import RetrievalHit

    class FakeKB:
        def __init__(self):
            self.calls = []
        def retrieve(self, query, top_k=5):
            self.calls.append((query, top_k))
            return [RetrievalHit(content="ctx-1", source="doc1.md", score=0.9)]
        def add_documents(self, docs, metadatas=None):
            pass
        def name(self):
            return "fake"

    fake_kb = FakeKB()
    monkeypatch.setattr(
        "bailian_rag_demo.app.api.get_kb", lambda settings: fake_kb
    )

    captured = {}
    def fake_call(**kwargs):
        captured.update(kwargs)
        return {
            "output": {"choices": [{"message": {"content": "answer with ctx"}}]},
            "usage": {"input_tokens": 12, "output_tokens": 34},
        }
    monkeypatch.setattr("dashscope.Generation.call", fake_call)

    resp = client.post(
        "/process",
        json={
            "input": [
                {"role": "user", "content": [{"type": "text", "text": "what?"}]}
            ],
            "session_id": "s1",
            "user_id": "u1",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["output"][0]["role"] == "assistant"
    assert body["output"][0]["content"][0]["text"] == "answer with ctx"
    assert body["session_id"] == "s1"
    assert body["usage"] == {"input_tokens": 12, "output_tokens": 34}
    assert fake_kb.calls == [("what?", 5)]
    assert "ctx-1" in captured["prompt"]


def test_process_handles_rag_empty(client, monkeypatch):
    class FakeKB:
        def retrieve(self, query, top_k=5):
            return []
        def add_documents(self, docs, metadatas=None):
            pass
        def name(self):
            return "fake"

    monkeypatch.setattr(
        "bailian_rag_demo.app.api.get_kb", lambda settings: FakeKB()
    )
    monkeypatch.setattr(
        "dashscope.Generation.call",
        lambda **kw: {"output": {"choices": [{"message": {"content": "ok"}}]}},
    )

    resp = client.post(
        "/process",
        json={"input": [{"role": "user", "content": [{"type": "text", "text": "q"}]}]},
    )
    assert resp.status_code == 200
    assert resp.json()["output"][0]["content"][0]["text"] == "ok"


def test_process_invalid_request_returns_422(client):
    resp = client.post("/process", json={"input": "not-a-list"})
    assert resp.status_code == 422