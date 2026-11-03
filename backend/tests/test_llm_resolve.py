"""Model auto-selection and fallback (no network: Google's replies are simulated)."""
import os
import sys

import pytest
from langchain_core.messages import AIMessage

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import llm  # noqa: E402


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "fake")
    llm._resolved = None
    llm._bad.clear()
    llm._cool.clear()
    llm._names_cache.update(at=0.0, names=[])
    llm.LAST_USED["model"] = None
    yield
    llm._resolved = None
    llm._bad.clear()
    llm._cool.clear()
    llm._names_cache.update(at=0.0, names=[])


def test_prefers_newest_stable_flash_over_lite_and_preview():
    names = ["gemini-2.0-flash", "gemini-2.5-flash-lite", "gemini-3-flash-preview", "gemini-2.5-pro", "gemini-3.1-flash-image", "gemini-3.5-flash"]
    assert llm.pick_model(names) == "gemini-3.5-flash"


def test_ranking_order_and_exclusions():
    names = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.8-flash-tts", "gemini-3.1-flash-lite", "gemini-3-flash-preview", "gemini-embedding-001", "gemma-4-31b-it"]
    assert llm.rank_models(names)[:4] == ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3-flash-preview", "gemini-3.1-flash-lite"]
    assert "gemini-3.8-flash-tts" not in llm.rank_models(names) and "gemma-4-31b-it" not in llm.rank_models(names)


def test_skips_unavailable_and_non_text_models():
    names = ["gemini-2.5-flash", "gemini-3-flash", "gemini-live-2.5-flash", "gemini-embedding-001", "gemini-2.5-flash-preview-tts"]
    assert llm.pick_model(names, bad={"gemini-3-flash"}) == "gemini-2.5-flash"


def test_falls_back_to_preview_then_lite_then_any():
    assert llm.pick_model(["gemini-3-flash-preview", "gemini-2.5-flash-lite"]) == "gemini-3-flash-preview"
    assert llm.pick_model(["gemini-2.5-flash-lite", "gemini-2.5-pro"]) == "gemini-2.5-flash-lite"
    assert llm.pick_model(["gemini-2.5-pro"]) == "gemini-2.5-pro"
    assert llm.pick_model(["text-embedding-004"]) is None


def test_env_override_wins_and_listing_is_cached(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "my-model")
    assert llm.resolve_model() == "my-model"
    monkeypatch.delenv("GEMINI_MODEL")
    calls = []
    monkeypatch.setattr(llm, "list_models", lambda key=None: (calls.append(1), ["gemini-2.5-flash", "gemini-3-flash"])[1])
    assert llm.resolve_model() == "gemini-3-flash" and llm.resolve_model() == "gemini-3-flash" and len(calls) == 1
    llm.mark_unavailable("gemini-3-flash")
    assert llm.resolve_model() == "gemini-2.5-flash"


def test_cooldown_skips_an_overloaded_model_temporarily(monkeypatch):
    monkeypatch.setattr(llm, "list_models", lambda key=None: ["gemini-3.8-flash", "gemini-3.6-flash"])
    assert llm.resolve_model() == "gemini-3.8-flash"
    llm.mark_unavailable("gemini-3.8-flash", cooldown=300)
    assert llm.resolve_model() == "gemini-3.6-flash"
    llm._cool["gemini-3.8-flash"] = 0  # cooldown expired
    llm._resolved = None
    assert llm.resolve_model() == "gemini-3.8-flash"


def test_error_classification():
    assert llm.is_model_missing(RuntimeError("GoogleModelNotFoundError: Error calling model 'x' (NOT_FOUND): 404"))
    assert llm.is_model_missing(RuntimeError("This model is no longer available to new users"))
    assert llm.is_overloaded(RuntimeError("GoogleAPIError: 503 UNAVAILABLE. This model is currently experiencing high demand."))
    assert llm.is_overloaded(RuntimeError("429 RESOURCE_EXHAUSTED"))
    assert llm.is_overloaded(RuntimeError("ReadTimeout: timed out"))
    assert not llm.is_overloaded(RuntimeError("400 INVALID_ARGUMENT: bad schema"))


class FakeModel:
    def __init__(self, name, outcome, log):
        self.name, self.outcome, self.log = name, outcome, log
        self.bound = None

    def bind_tools(self, tools):
        self.bound = tools
        return self

    def invoke(self, messages, *a, **k):
        self.log.append(self.name)
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return AIMessage(content=f"from {self.name}")


def install(monkeypatch, outcomes):
    log = []
    monkeypatch.setattr(llm, "list_models", lambda key=None: list(outcomes))
    monkeypatch.setattr(llm, "_make", lambda name: FakeModel(name, outcomes[name], log))
    return log


def test_resilient_chat_falls_back_on_503_and_remembers(monkeypatch):
    log = install(monkeypatch, {"gemini-3.8-flash": RuntimeError("503 UNAVAILABLE high demand"), "gemini-3.6-flash": None})
    m = llm.gemini()
    assert llm.text_of(m.invoke("hi")) == "from gemini-3.6-flash"
    assert log == ["gemini-3.8-flash", "gemini-3.6-flash"]
    log.clear()
    assert llm.text_of(m.invoke("again")) == "from gemini-3.6-flash"  # the overloaded one is skipped, not retried
    assert log == ["gemini-3.6-flash"] and llm.LAST_USED["model"] == "gemini-3.6-flash"


def test_resilient_chat_retires_missing_models_and_keeps_tools_bound(monkeypatch):
    log = install(monkeypatch, {"gemini-3.8-flash": RuntimeError("NOT_FOUND 404"), "gemini-3.5-flash": None})
    m = llm.gemini().bind_tools(["tool-a"])
    assert llm.text_of(m.invoke("hi")) == "from gemini-3.5-flash"
    assert "gemini-3.8-flash" in llm._bad


def test_resilient_chat_does_not_mask_real_errors(monkeypatch):
    install(monkeypatch, {"gemini-3.8-flash": ValueError("400 INVALID_ARGUMENT bad request"), "gemini-3.6-flash": None})
    with pytest.raises(ValueError):
        llm.gemini().invoke("hi")


def test_resilient_chat_gives_up_with_the_last_error_when_everything_is_down(monkeypatch):
    install(monkeypatch, {"gemini-3.8-flash": RuntimeError("503 UNAVAILABLE"), "gemini-3.6-flash": RuntimeError("503 UNAVAILABLE again")})
    with pytest.raises(RuntimeError, match="503"):
        llm.gemini().invoke("hi")


def test_explicit_model_is_exact_and_never_swapped(monkeypatch):
    log = install(monkeypatch, {"my-pinned-model": RuntimeError("503 UNAVAILABLE"), "gemini-3.6-flash": None})
    m = llm.gemini("my-pinned-model")
    with pytest.raises(RuntimeError, match="503"):
        m.invoke("hi")
    assert log == ["my-pinned-model"]
    monkeypatch.setenv("GEMINI_MODEL", "my-pinned-model")
    assert not isinstance(llm.gemini(), llm.ResilientChat)


def test_model_listing_uses_a_verified_certifi_context(monkeypatch):
    import ssl
    seen = {}

    class R:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self, *a): return b'{"models": [{"name": "models/gemini-3-flash", "supportedGenerationMethods": ["generateContent"]}]}'

    def fake_urlopen(url, timeout=None, context=None):
        seen["ctx"] = context
        return R()

    monkeypatch.setattr(llm.urllib.request, "urlopen", fake_urlopen)
    assert llm.list_models("k") == ["gemini-3-flash"]
    assert isinstance(seen["ctx"], ssl.SSLContext) and seen["ctx"].verify_mode == ssl.CERT_REQUIRED  # never disables verification


def test_listing_failure_gives_actionable_error(monkeypatch):
    monkeypatch.setattr(llm, "list_models", lambda key=None: (_ for _ in ()).throw(OSError("boom")))
    with pytest.raises(RuntimeError, match="GEMINI_MODEL"):
        llm.resolve_model()


def test_never_picks_non_chat_models_even_when_everything_else_is_down():
    names = ["gemini-3.5-transcribe", "gemini-omni-1.1-flash", "gemini-4-argon", "gemini-nano-banana-2.1", "gemini-3.8-flash-tts",
             "gemini-3.1-flash-image", "gemini-flash-latest", "gemini-2.5-pro-preview-tts", "gemini-3.1-pro-preview-customtools",
             "gemini-3.6-flash", "gemini-2.5-pro"]
    ranked = llm.rank_models(names)
    assert ranked == ["gemini-3.6-flash", "gemini-2.5-pro"]
    assert llm.pick_model(names, bad={"gemini-3.6-flash", "gemini-2.5-pro"}) is None  # nothing silly is substituted


def test_usage_is_counted_per_model(monkeypatch):
    log = install(monkeypatch, {"gemini-3.8-flash": RuntimeError("503 UNAVAILABLE"), "gemini-3.6-flash": None})
    llm.USAGE.clear()
    m = llm.gemini()
    m.invoke("a")
    m.invoke("b")
    assert llm.USAGE == {"gemini-3.6-flash": 2}


def test_quota_errors_are_recognised_and_explained(monkeypatch):
    e = RuntimeError("GoogleRateLimitError: 429 RESOURCE_EXHAUSTED. You exceeded your current quota ... free_tier_requests, limit: 20")
    assert llm.is_quota(e) and not llm.is_quota(RuntimeError("503 UNAVAILABLE"))
    assert "enable billing" in llm.QUOTA_MESSAGE and "20 requests" in llm.QUOTA_MESSAGE
    log = install(monkeypatch, {"gemini-3.8-flash": e, "gemini-3.6-flash": None})
    assert llm.text_of(llm.gemini().invoke("hi")) == "from gemini-3.6-flash"  # another model's quota may still be available


def test_preferred_model_is_tried_first_then_normal_fallback(monkeypatch):
    monkeypatch.setenv("GEMINI_PREFERRED", "gemini-3.1-flash-lite")
    monkeypatch.setattr(llm, "list_models", lambda key=None: ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.1-flash-lite"])
    assert llm.resolve_model() == "gemini-3.1-flash-lite"           # not the newest/priciest
    llm.mark_unavailable("gemini-3.1-flash-lite", cooldown=300)
    assert llm.resolve_model() == "gemini-3.8-flash"                  # overloaded/out of quota -> usual ranking
    monkeypatch.setenv("GEMINI_PREFERRED", "not-a-listed-model")
    llm._cool.clear(); llm._resolved = None
    assert llm.resolve_model() == "gemini-3.8-flash"                  # unknown preference is ignored
