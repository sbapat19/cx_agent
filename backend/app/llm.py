"""Model access. Gemini via langchain-google-genai; a scripted fake model for offline tests.

Set GOOGLE_API_KEY (in .env) and optionally GEMINI_MODEL. Run `python scripts/check_gemini.py` to list the models
your key can use and test a call.
"""
import json
import os
import re
import time
import urllib.request
import warnings

warnings.filterwarnings("ignore", message=".*fixed sampling defaults.*")  # Gemini 3.x ignores temperature; harmless

from langchain_core.messages import AIMessage

# GEMINI_MODEL in .env always wins. If it is not set, the app asks Google which models YOUR key can use and picks
# the newest suitable flash-family model (model names get retired, so a hard-coded default goes stale).
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "auto")

_EXCLUDE = ("image", "tts", "live", "audio", "embedding", "robotics", "computer", "vision", "aqa", "gemma", "learnlm", "imagen", "veo",
            "transcribe", "omni", "customtools", "banana", "lyria", "antigravity", "research", "native")
_resolved = None
_bad: set = set()


def _ssl_context():
    """Use certifi's CA bundle when available. Python installed from python.org on macOS often has no system certificates
    ('CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate'); certifi is already a dependency of the Gemini libraries."""
    import ssl
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def list_models(key: str | None = None) -> list[str]:
    """Names of models this key can call with generateContent (no 'models/' prefix)."""
    key = key or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GOOGLE_API_KEY is not set. Add it to .env")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}&pageSize=200"
    with urllib.request.urlopen(url, timeout=30, context=_ssl_context()) as r:
        data = json.load(r)
    return sorted(m["name"].replace("models/", "") for m in data.get("models", [])
                  if "generateContent" in m.get("supportedGenerationMethods", []))


_CHAT = re.compile(r"^gemini-\d+(?:\.\d+)?-(?:flash|pro)(?:-|$)")


def rank_models(names: list[str], bad: set | None = None) -> list[str]:
    """Candidates in preference order: newest stable flash first, then flash previews, then flash-lite, then pro.
    Only text/chat flash and pro families are ever considered (never transcription, image, TTS, live, embedding, omni, etc.)."""
    bad = bad or set()
    ok = [n for n in names if _CHAT.match(n) and n not in bad and not any(x in n for x in _EXCLUDE)]

    def ver(n):
        m = re.match(r"gemini-(\d+(?:\.\d+)?)", n)
        return float(m.group(1)) if m else 0.0

    stable = [n for n in ok if re.fullmatch(r"gemini-\d+(?:\.\d+)?-flash(?:-\d+)?", n)]
    preview = [n for n in ok if re.match(r"gemini-\d+(?:\.\d+)?-flash(?!-lite)", n) and "preview" in n]
    lite = [n for n in ok if "flash-lite" in n]
    out = []
    for group in (stable, preview, lite, ok):
        for n in sorted(group, key=lambda n: (ver(n), n), reverse=True):
            if n not in out:
                out.append(n)
    return out


def pick_model(names: list[str], bad: set | None = None) -> str | None:
    ranked = rank_models(names, bad)
    return ranked[0] if ranked else None


_cool: dict = {}  # model name -> time until which it is skipped (overloaded / rate limited)
_names_cache: dict = {"at": 0.0, "names": []}
LAST_USED: dict = {"model": None}
USAGE: dict = {}  # model name -> number of successful calls (reported by the eval runner)


def _available_names() -> list[str]:
    if time.time() - _names_cache["at"] > 600 or not _names_cache["names"]:
        _names_cache["names"] = list_models()
        _names_cache["at"] = time.time()
    return _names_cache["names"]


def resolve_model(force: bool = False) -> str:
    """Model name to use: GEMINI_MODEL if set, otherwise the best candidate that is not retired or cooling down."""
    global _resolved
    env = os.getenv("GEMINI_MODEL")
    if env and env.lower() != "auto":
        return env
    now = time.time()
    skip = set(_bad) | {n for n, until in _cool.items() if until > now}
    if _resolved and not force and _resolved not in skip:
        return _resolved
    try:
        names = _available_names()
    except Exception as e:
        raise RuntimeError(f"Could not ask Google which models your key can use ({type(e).__name__}: {str(e)[:120]}). "
                           "Set GEMINI_MODEL=<model name> in .env to skip this lookup. Run scripts/check_gemini.py for help.") from e
    pref = (os.getenv("GEMINI_PREFERRED") or "").strip()
    if pref and pref in names and pref not in skip:
        _resolved = pref  # preferred (e.g. the cheapest) model first; the usual automatic fallback still applies if it fails
        return pref
    name = pick_model(names, skip)
    if not name:
        # everything is cooling down or retired: try the least-recently failed one rather than giving up
        name = pick_model(names, set(_bad))
    if not name:
        raise RuntimeError("No usable Gemini model found for this key. Run scripts/check_gemini.py and set GEMINI_MODEL in .env")
    _resolved = name
    return name


def mark_unavailable(name: str, cooldown: float | None = None):
    """Retired model (cooldown=None): never use again this run. Overloaded/rate-limited: skip it for `cooldown` seconds."""
    global _resolved
    if cooldown is None:
        _bad.add(name)
    else:
        _cool[name] = time.time() + cooldown
    if _resolved == name:
        _resolved = None


def is_model_missing(exc: Exception) -> bool:
    t = f"{type(exc).__name__} {exc}"
    return "NOT_FOUND" in t or "NotFound" in t or "no longer available" in t


def is_quota(exc: Exception) -> bool:
    t = f"{type(exc).__name__} {exc}".lower()
    return "resource_exhausted" in t or "quota" in t or "429" in t


QUOTA_MESSAGE = ("Your Gemini API key has used up its quota (the free tier allows only about 20 requests per model per day, and one "
                 "conversation turn uses several). Wait for the daily reset or enable billing for the key's Google project in "
                 "Google AI Studio, then try again.")


def is_overloaded(exc: Exception) -> bool:
    t = f"{type(exc).__name__} {exc}".lower()
    return any(k in t for k in ("503", "unavailable", "high demand", "overloaded", "429", "resource_exhausted", "quota",
                                "timeout", "timed out", "deadline", "502", "504"))


def text_of(msg) -> str:
    """Extract plain text from a model message (Gemini may return a list of parts)."""
    c = getattr(msg, "content", msg)
    if isinstance(c, str):
        return c
    parts = []
    for p in c or []:
        if isinstance(p, str):
            parts.append(p)
        elif isinstance(p, dict) and p.get("type") == "text":
            parts.append(p.get("text", ""))
    return "".join(parts)


def _make(name: str):
    from langchain_google_genai import ChatGoogleGenerativeAI

    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GOOGLE_API_KEY is not set. Add it to .env")
    # max_retries=0: our own fallback (below) switches models quickly instead of the SDK backing off on an overloaded one
    return ChatGoogleGenerativeAI(model=name, temperature=0, google_api_key=key, max_retries=0,
                                  timeout=float(os.getenv("GEMINI_TIMEOUT", "45")))


class ResilientChat:
    """Chat model that falls back to the next available Gemini model when one is retired (404) or overloaded (503/429/timeout).

    Each call is independent, so switching models mid-conversation is safe (the full message history is sent every time)
    and no tool action is ever replayed.
    """

    def __init__(self, tools=None):
        self.tools = tools

    @property
    def _advisor_model_name(self):
        return LAST_USED["model"]

    def bind_tools(self, tools):
        return ResilientChat(tools)

    def invoke(self, messages, *a, **k):
        last = None
        for _ in range(8):
            name = resolve_model()
            m = _make(name)
            if self.tools:
                m = m.bind_tools(self.tools)
            try:
                out = m.invoke(messages, *a, **k)
                LAST_USED["model"] = name
                USAGE[name] = USAGE.get(name, 0) + 1
                return out
            except Exception as e:
                if is_model_missing(e):
                    mark_unavailable(name)
                elif is_quota(e):
                    mark_unavailable(name, cooldown=900)  # try another model's quota; this one is skipped for 15 minutes
                elif is_overloaded(e):
                    mark_unavailable(name, cooldown=300)
                else:
                    raise
                last = e
        raise last


def gemini(model: str | None = None):
    """model=None -> automatic choice with fallback. An explicit name (argument or GEMINI_MODEL) is used exactly, never swapped."""
    explicit = model or (os.getenv("GEMINI_MODEL") if (os.getenv("GEMINI_MODEL") or "").lower() not in ("", "auto") else None)
    if explicit:
        m = _make(explicit)
        m._advisor_model_name = explicit
        LAST_USED["model"] = explicit
        return m
    resolve_model()  # fail fast with a clear message if the key or lookup is broken
    return ResilientChat()


class ScriptedModel:
    """Offline stand-in used by tests and demos without a key.

    `script` is a list of callables or AIMessage objects consumed in order; a callable gets the message list.
    bind_tools() returns self so the agent loop is identical to the real model path.
    """

    def __init__(self, script):
        self.script = list(script)
        self.calls = 0

    def bind_tools(self, tools):
        return self

    def invoke(self, messages, *a, **k):
        self.calls += 1
        if not self.script:
            return AIMessage(content="(scripted model has no more steps)")
        step = self.script.pop(0)
        return step(messages) if callable(step) else step


def tool_call(name, args, call_id=None):
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": call_id or f"call_{name}"}])
