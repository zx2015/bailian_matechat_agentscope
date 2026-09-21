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
    return Settings(
        DASHSCOPE_API_KEY="sk-test",
        ALIBABA_CLOUD_ACCESS_KEY_ID="ak-test",
        ALIBABA_CLOUD_ACCESS_KEY_SECRET="ak-secret-test",
        BAILIAN_WORKSPACE_ID="ws-test",
        BAILIAN_INDEX_ID="idx-test",
    )


def _fake_model_call(text, usage=None):
    """Build an async stand-in for `DashScopeChatModel.__call__` that returns
    a plain-text (non-tool-call) response, so the ReAct loop exits after a
    single reasoning step."""
    from agentscope.message import TextBlock
    from agentscope.model import ChatResponse
    from agentscope.model._model_usage import ChatUsage

    async def _call(self, *args, **kwargs):
        return ChatResponse(
            content=[TextBlock(type="text", text=text)],
            usage=ChatUsage(**usage, time=0.01) if usage else None,
        )

    return _call


def test_runtime_agent_assembles_prompt_with_rag_context(monkeypatch):
    from agentscope.model import DashScopeChatModel
    from bailian_rag_demo.rag.base import RetrievalHit

    kb = BaiLianKB(_settings())
    monkeypatch.setattr(kb, "retrieve", lambda q, top_k=5: [
        RetrievalHit(content="ctx-1", source="doc1.md", score=0.9)
    ])

    captured = {}

    async def fake_call(self, prompt, *args, **kwargs):
        captured["prompt"] = prompt
        from agentscope.message import TextBlock
        from agentscope.model import ChatResponse
        from agentscope.model._model_usage import ChatUsage

        return ChatResponse(
            content=[TextBlock(type="text", text="OK answer")],
            usage=ChatUsage(input_tokens=5, output_tokens=7, time=0.01),
        )

    monkeypatch.setattr(DashScopeChatModel, "__call__", fake_call)

    agent = RuntimeAgent(settings=_settings())
    out, usage, sources = agent.run("what is X?", kb, session_id="s1")

    assert out == "OK answer"
    assert usage == {"input_tokens": 5, "output_tokens": 7}
    assert "ctx-1" in str(captured["prompt"])
    assert "doc1.md" in str(captured["prompt"])
    assert "what is X?" in str(captured["prompt"])
    assert sources == [RetrievalHit(content="ctx-1", source="doc1.md", score=0.9)]


def test_runtime_agent_continues_when_rag_returns_empty(monkeypatch):
    from agentscope.model import DashScopeChatModel

    kb = BaiLianKB(_settings())
    monkeypatch.setattr(kb, "retrieve", lambda q, top_k=5: [])

    monkeypatch.setattr(
        DashScopeChatModel, "__call__", _fake_model_call("no context answer")
    )

    agent = RuntimeAgent(settings=_settings())
    out, usage, sources = agent.run("nope?", kb)
    assert out == "no context answer"
    assert usage is None
    assert sources == []


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

    from agentscope.model import DashScopeChatModel, ChatResponse
    from agentscope.model._model_usage import ChatUsage
    from agentscope.message import TextBlock

    captured = {}

    async def fake_call(self, prompt, *args, **kwargs):
        captured["prompt"] = prompt
        return ChatResponse(
            content=[TextBlock(type="text", text="answer with ctx")],
            usage=ChatUsage(input_tokens=12, output_tokens=34, time=0.01),
        )

    monkeypatch.setattr(DashScopeChatModel, "__call__", fake_call)

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
    assert "ctx-1" in str(captured["prompt"])
    assert "doc1.md" in str(captured["prompt"])
    assert body["references"] == [{"source": "doc1.md", "score": 0.9}]


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
        "bailian_rag_demo.app.runtime_agent.DashScopeChatModel.__call__",
        _fake_model_call("ok"),
    )

    resp = client.post(
        "/process",
        json={"input": [{"role": "user", "content": [{"type": "text", "text": "q"}]}]},
    )
    assert resp.status_code == 200
    assert resp.json()["output"][0]["content"][0]["text"] == "ok"
    assert resp.json()["references"] is None


def test_process_invalid_request_returns_422(client):
    resp = client.post("/process", json={"input": "not-a-list"})
    assert resp.status_code == 422