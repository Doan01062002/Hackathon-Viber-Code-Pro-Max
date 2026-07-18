import hashlib
import io

import pytest
from ai_service import engine as engine_module


def test_resolve_model_path_downloads_and_verifies_artifact(monkeypatch, tmp_path) -> None:
    payload = b"serialized-model"
    monkeypatch.setenv("AI_MODEL_URL", "https://example.test/model.pkl")
    monkeypatch.setenv("AI_MODEL_SHA256", hashlib.sha256(payload).hexdigest())
    monkeypatch.setattr(engine_module.tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(
        engine_module.urllib.request,
        "urlopen",
        lambda _url, timeout: io.BytesIO(payload),
    )

    resolved_path = engine_module._resolve_model_path(str(tmp_path / "missing.pkl"))

    assert resolved_path == str(tmp_path / "srrm-model.pkl")
    assert (tmp_path / "srrm-model.pkl").read_bytes() == payload


def test_resolve_model_path_rejects_non_https_url(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("AI_MODEL_URL", "http://example.test/model.pkl")

    with pytest.raises(engine_module.AIEngineError, match="HTTPS"):
        engine_module._resolve_model_path(str(tmp_path / "missing.pkl"))
