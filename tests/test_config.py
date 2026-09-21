import os
import pytest
from bailian_rag_demo.config import Settings, load_settings


def test_load_settings_with_all_required(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test")
    monkeypatch.setenv("BAILIAN_APP_ID", "app-test")
    settings = load_settings()
    assert settings.DASHSCOPE_API_KEY == "sk-test"
    assert settings.BAILIAN_APP_ID == "app-test"
    assert settings.BAILIAN_RAG_TOP_K == 5  # default
    assert settings.RAG_TIMEOUT_SEC == 10.0  # default


def test_load_settings_with_custom_top_k(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test")
    monkeypatch.setenv("BAILIAN_APP_ID", "app-test")
    monkeypatch.setenv("BAILIAN_RAG_TOP_K", "10")
    settings = load_settings()
    assert settings.BAILIAN_RAG_TOP_K == 10


def test_load_settings_missing_api_key(monkeypatch, capsys):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setenv("BAILIAN_APP_ID", "app-test")
    with pytest.raises(SystemExit) as exc_info:
        load_settings()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "DASHSCOPE_API_KEY" in captured.err


def test_load_settings_missing_app_id(monkeypatch, capsys):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test")
    monkeypatch.delenv("BAILIAN_APP_ID", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        load_settings()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "BAILIAN_APP_ID" in captured.err