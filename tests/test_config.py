import pytest
from bailian_rag_demo.config import Settings, load_settings


def _set_all_required(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test")
    monkeypatch.setenv("ALIBABA_CLOUD_ACCESS_KEY_ID", "ak-test")
    monkeypatch.setenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET", "ak-secret-test")
    monkeypatch.setenv("BAILIAN_WORKSPACE_ID", "ws-test")
    monkeypatch.setenv("BAILIAN_INDEX_ID", "idx-test")


def test_load_settings_with_all_required(monkeypatch):
    _set_all_required(monkeypatch)
    settings = load_settings()
    assert settings.DASHSCOPE_API_KEY == "sk-test"
    assert settings.ALIBABA_CLOUD_ACCESS_KEY_ID == "ak-test"
    assert settings.ALIBABA_CLOUD_ACCESS_KEY_SECRET == "ak-secret-test"
    assert settings.BAILIAN_WORKSPACE_ID == "ws-test"
    assert settings.BAILIAN_INDEX_ID == "idx-test"
    assert settings.BAILIAN_APP_ID is None  # deprecated, optional now
    assert settings.BAILIAN_RAG_TOP_K == 5  # default
    assert settings.RAG_TIMEOUT_SEC == 10.0  # default
    assert settings.BAILIAN_REGION_ID == "cn-beijing"  # default


def test_load_settings_with_custom_top_k(monkeypatch):
    _set_all_required(monkeypatch)
    monkeypatch.setenv("BAILIAN_RAG_TOP_K", "10")
    settings = load_settings()
    assert settings.BAILIAN_RAG_TOP_K == 10


def test_load_settings_missing_api_key(monkeypatch, capsys):
    _set_all_required(monkeypatch)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        load_settings()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "DASHSCOPE_API_KEY" in captured.err


def test_load_settings_missing_workspace_id(monkeypatch, capsys):
    _set_all_required(monkeypatch)
    monkeypatch.delenv("BAILIAN_WORKSPACE_ID", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        load_settings()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "BAILIAN_WORKSPACE_ID" in captured.err


def test_load_settings_missing_index_id(monkeypatch, capsys):
    _set_all_required(monkeypatch)
    monkeypatch.delenv("BAILIAN_INDEX_ID", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        load_settings()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "BAILIAN_INDEX_ID" in captured.err


def test_load_settings_missing_access_key(monkeypatch, capsys):
    _set_all_required(monkeypatch)
    monkeypatch.delenv("ALIBABA_CLOUD_ACCESS_KEY_ID", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        load_settings()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "ALIBABA_CLOUD_ACCESS_KEY_ID" in captured.err
