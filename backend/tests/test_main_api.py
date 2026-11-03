"""API-level tests (no network): retired-model retry and error reporting."""
import json
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import agent, db, llm  # noqa: E402
from app.llm import ScriptedModel  # noqa: E402


@pytest.fixture()
def client(monkeypatch):
    d = tempfile.mkdtemp()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{d}/api.db")
    monkeypatch.setenv("GOOGLE_API_KEY", "fake")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    db.reset_engine(f"sqlite:///{d}/api.db")
    agent.SESSIONS.clear()
    llm._resolved = None
    llm._bad.clear()
    import main
    with TestClient(main.app) as c:
        yield c
    llm._resolved = None
    llm._bad.clear()


class RetiredModel:
    _advisor_model_name = "gemini-2.5-flash"

    def bind_tools(self, t):
        return self

    def invoke(self, *a, **k):
        raise RuntimeError("GoogleModelNotFoundError: (NOT_FOUND): 404 This model is no longer available to new users")


def good(name):
    m = ScriptedModel([AIMessage(content=json.dumps({"intent": "OUT_OF_SCOPE", "reason": "t"}))])
    m._advisor_model_name = name
    return m


def test_retired_model_is_skipped_and_the_request_is_retried(client, monkeypatch):
    models = [RetiredModel(), good("gemini-3-flash")]
    monkeypatch.setattr(llm, "gemini", lambda model=None: models.pop(0))
    r = client.post("/chat", json={"message": "hello", "customer_id": "cust_ava"})
    assert r.status_code == 200 and r.json()["route"] == "OUT_OF_SCOPE"
    assert "gemini-2.5-flash" in llm._bad


def test_explicit_model_setting_is_never_silently_swapped(client, monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")
    monkeypatch.setattr(llm, "gemini", lambda model=None: RetiredModel())
    r = client.post("/chat", json={"message": "hello", "customer_id": "cust_ava"})
    assert r.status_code == 502 and "gemini-2.5-flash" in r.json()["detail"] and "NOT_FOUND" in r.json()["detail"]


def test_missing_key_gives_a_clear_503(client, monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY")
    assert client.post("/chat", json={"message": "hi"}).status_code == 503


def test_unknown_customer_rejected(client):
    assert client.post("/chat", json={"message": "hi", "customer_id": "cust_nobody"}).status_code == 400


def test_session_cannot_switch_customer(client, monkeypatch):
    monkeypatch.setattr(llm, "gemini", lambda model=None: good("m"))
    sid = client.post("/chat", json={"message": "hi", "customer_id": "cust_ava"}).json()["session_id"]
    monkeypatch.setattr(llm, "gemini", lambda model=None: good("m"))
    r = client.post("/chat", json={"message": "hi", "customer_id": "cust_ben", "session_id": sid})
    assert r.status_code == 403


def test_debug_stage_db_works_locally_and_is_hidden_otherwise(client, monkeypatch):
    r = client.get("/debug/stage/db")
    assert r.status_code in (200, 404)  # TestClient's host is 'testclient', which is not local: must be hidden
    assert r.status_code == 404
    monkeypatch.setenv("ENABLE_DEBUG", "0")
    assert client.get("/debug/stage/db", headers={}).status_code == 404


def test_eval_endpoints_are_local_only(client):
    assert client.post("/debug/eval/start").status_code == 404
    assert client.get("/debug/eval/status").status_code == 404
    assert client.get("/debug/timings").status_code == 404


def test_eval_stop_is_local_only(client):
    assert client.post("/debug/eval/stop").status_code == 404


def test_quota_exhaustion_returns_a_plain_429_explanation(client, monkeypatch):
    class Quota:
        def bind_tools(self, t): return self
        def invoke(self, *a, **k): raise RuntimeError("GoogleRateLimitError: 429 RESOURCE_EXHAUSTED quota exceeded")
    monkeypatch.setattr(llm, "gemini", lambda model=None: Quota())
    r = client.post("/chat", json={"message": "hi", "customer_id": "cust_ava"})
    assert r.status_code == 429 and "enable billing" in r.json()["detail"]


def test_public_site_protections(client, monkeypatch):
    import main
    # message length cap
    r = client.post("/chat", json={"message": "x" * (main.MAX_MESSAGE_CHARS + 1)})
    assert r.status_code == 400
    # per-visitor rate limit (checked before any model call)
    monkeypatch.setattr(main, "RATE_PER_WINDOW", 2)
    monkeypatch.setattr(main, "RATE_WINDOW_S", 600)
    main._HITS.clear()
    monkeypatch.setattr(agent, "run_turn", lambda *a, **k: {"response": "ok"})
    monkeypatch.setattr(llm, "gemini", lambda *a, **k: object())
    assert client.post("/chat", json={"message": "hi"}).status_code == 200
    assert client.post("/chat", json={"message": "hi"}).status_code == 200
    assert client.post("/chat", json={"message": "hi"}).status_code == 429
    # daily cap for all visitors
    monkeypatch.setattr(main, "RATE_PER_WINDOW", 0)
    monkeypatch.setattr(main, "DAILY_CAP", 1)
    main._DAY.update(date=None, n=0)
    assert client.post("/chat", json={"message": "hi"}).status_code == 200
    assert client.post("/chat", json={"message": "hi"}).status_code == 429


def test_production_mode_hides_debug_and_reset(client, monkeypatch):
    import main
    monkeypatch.setattr(main, "PROD", True)
    assert client.post("/demo/reset").status_code == 404
    assert client.get("/debug/timings").status_code == 404
    assert client.post("/debug/eval/start").status_code == 404
    assert client.get("/api/customers").status_code == 200  # the UI's /api prefix is understood
