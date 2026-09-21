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