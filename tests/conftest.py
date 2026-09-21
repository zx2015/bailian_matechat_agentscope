import pytest
from fastapi.testclient import TestClient

from bailian_rag_demo.app.api import create_app
from bailian_rag_demo.config import Settings


@pytest.fixture
def fake_settings():
    return Settings(
        DASHSCOPE_API_KEY="sk-test",
        ALIBABA_CLOUD_ACCESS_KEY_ID="ak-test",
        ALIBABA_CLOUD_ACCESS_KEY_SECRET="ak-secret-test",
        BAILIAN_WORKSPACE_ID="ws-test",
        BAILIAN_INDEX_ID="idx-test",
    )


@pytest.fixture
def client(fake_settings, monkeypatch):
    monkeypatch.setattr(
        "bailian_rag_demo.app.api.load_settings", lambda: fake_settings
    )
    app = create_app(settings=fake_settings)
    return TestClient(app)