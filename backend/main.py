"""FastAPI shell for the independent Armani Beauty advisor prototype (fictional data, simulated transactions)."""
import os
import time
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from app import agent, llm  # noqa: E402
from app.db import init_db, jl, one, rows, execute  # noqa: E402
from app.seed import seed_all  # noqa: E402

app = FastAPI(title="Independent beauty advisor prototype (not affiliated with Armani Beauty, L'Oreal or Sierra)")

ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGIN", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, allow_credentials=False, allow_methods=["*"], allow_headers=["*"])


PROD = os.getenv("APP_ENV", "").lower() == "production"
RATE_PER_WINDOW = int(os.getenv("RATE_LIMIT_MESSAGES", "20" if PROD else "0"))   # messages per IP per window; 0 = off
RATE_WINDOW_S = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "600"))
DAILY_CAP = int(os.getenv("DAILY_MESSAGE_CAP", "1500" if PROD else "0"))          # total model-backed messages per day, all visitors; 0 = off
MAX_MESSAGE_CHARS = int(os.getenv("MAX_MESSAGE_CHARS", "1000"))
_HITS: dict[str, list] = {}
_DAY = {"date": None, "n": 0}


def _client_ip(request: Request) -> str:
    if PROD:
        fwd = request.headers.get("x-forwarded-for", "")
        if fwd:
            return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_limits(request: Request):
    """Protects the Gemini bill on a public site: per-visitor rate limit plus a daily cap for everyone."""
    now = time.time()
    if RATE_PER_WINDOW > 0:
        ip = _client_ip(request)
        hits = [t for t in _HITS.get(ip, []) if now - t < RATE_WINDOW_S]
        if len(hits) >= RATE_PER_WINDOW:
            raise HTTPException(429, "You have sent a lot of messages in a short time. Please wait a few minutes and try again.")
        hits.append(now)
        _HITS[ip] = hits
        if len(_HITS) > 5000:  # keep memory bounded
            for k in [k for k, v in _HITS.items() if not v or now - v[-1] > RATE_WINDOW_S]:
                _HITS.pop(k, None)
    if DAILY_CAP > 0:
        today = time.strftime("%Y-%m-%d", time.gmtime())
        if _DAY["date"] != today:
            _DAY.update(date=today, n=0)
        if _DAY["n"] >= DAILY_CAP:
            raise HTTPException(429, "This demo has reached its daily message limit. Please come back tomorrow.")
        _DAY["n"] += 1


@app.middleware("http")
async def _strip_api_prefix(request: Request, call_next):
    # The UI calls /api/...; in production one service serves both the UI and the API.
    path = request.scope["path"]
    if path.startswith("/api/"):
        request.scope["path"] = path[4:]
    return await call_next(request)


@app.on_event("startup")
def _startup():
    init_db()
    if not one("SELECT id FROM products LIMIT 1"):
        seed_all()


class ChatRequest(BaseModel):
    message: str
    customer_id: str | None = None
    session_id: str | None = None


@app.get("/health")
def health():
    return {"status": "ok", "model": os.getenv("GEMINI_MODEL") or "auto (picked from your key's available models)",
            "model_in_use": llm.LAST_USED["model"] or llm._resolved, "gemini_key_set": bool(os.getenv("GOOGLE_API_KEY"))}


@app.get("/customers")
def customers():
    return {"fictional": True, "customers": rows("SELECT id, name, blurb FROM customers ORDER BY id")}


@app.post("/chat")
def chat(req: ChatRequest, request: Request):
    if not req.message.strip():
        raise HTTPException(400, "Message cannot be empty")
    if len(req.message) > MAX_MESSAGE_CHARS:
        raise HTTPException(400, f"Please keep messages under {MAX_MESSAGE_CHARS} characters.")
    _check_limits(request)
    if not os.getenv("GOOGLE_API_KEY"):
        raise HTTPException(503, "GOOGLE_API_KEY not set. Add it to .env to use the advisor.")
    if req.customer_id and not one("SELECT id FROM customers WHERE id=:i", i=req.customer_id):
        raise HTTPException(400, "Unknown demo customer")
    sid = req.session_id or str(uuid.uuid4())
    for attempt in (1, 2):
        model = None
        try:
            model = llm.gemini()
            return agent.run_turn(sid, req.customer_id, req.message.strip(), model=model)
        except PermissionError as e:
            raise HTTPException(403, str(e))
        except Exception as e:  # model/network errors: report plainly
            name = getattr(model, "_advisor_model_name", None)
            if attempt == 1 and name and not os.getenv("GEMINI_MODEL") and llm.is_model_missing(e):
                llm.mark_unavailable(name)  # model was retired for this key: pick another and retry once
                continue
            if llm.is_quota(e):
                raise HTTPException(429, llm.QUOTA_MESSAGE)
            raise HTTPException(502, f"The model call failed ({name or 'model not chosen'}): {type(e).__name__}: {str(e)[:300]}")


@app.get("/preferences")
def preferences(customer_id: str):
    r = one("SELECT * FROM saved_preferences WHERE customer_id=:c", c=customer_id)
    return {"saved": bool(r), "preferences": jl(r["data"]) if r else None, "updated_at": r["updated_at"] if r else None}


@app.delete("/preferences")
def delete_preferences(customer_id: str):
    execute("DELETE FROM saved_preferences WHERE customer_id=:c", c=customer_id)
    return {"deleted": True}


@app.post("/demo/reset")
def reset():
    """Reset fictional demo data (customers, orders, cases, preferences) and clear sessions. Disabled on the public site."""
    if PROD:
        raise HTTPException(404)
    agent.SESSIONS.clear()
    return {"reset": True, **seed_all()}


@app.get("/debug/stage/{stage}")
def debug_stage(stage: str, request: Request, model: str | None = None):
    """Local-only diagnostics (db, list, init, ping, tools). Never returns the key. Disabled off localhost or with ENABLE_DEBUG=0."""
    if PROD or os.getenv("ENABLE_DEBUG", "1") == "0" or (request.client and request.client.host not in ("127.0.0.1", "::1", "localhost")):
        raise HTTPException(404)
    t0 = time.time()
    try:
        if stage == "db":
            out = rows("SELECT COUNT(*) AS products FROM products")
        elif stage == "list":
            out = llm.list_models()[:60]
        elif stage == "init":
            out = getattr(llm.gemini(), "_advisor_model_name", None)
        elif stage == "ping":
            out = llm.text_of(llm.gemini(model).invoke("Reply with the single word: ready"))
        elif stage == "tools":
            from app.tools import ToolContext, build_tools
            tools = build_tools(ToolContext("cust_ava", "dbg", 1), ["get_policy"])
            r = llm.gemini().bind_tools(tools).invoke("What is the exchange policy? Use the get_policy tool with topic exchanges.")
            out = {"text": llm.text_of(r), "tool_calls": getattr(r, "tool_calls", None)}
        else:
            raise HTTPException(404)
    except HTTPException:
        raise
    except Exception as e:
        return {"stage": stage, "ok": False, "seconds": round(time.time() - t0, 1), "error": f"{type(e).__name__}: {str(e)[:500]}"}
    return {"stage": stage, "ok": True, "seconds": round(time.time() - t0, 1), "result": out}


@app.get("/debug/timings")
def debug_timings(request: Request):
    _debug_ok(request)
    return {"recent_model_calls": agent.TIMINGS[-30:]}


# ---- local-only: run the eval suite in a separate process (own database) and read its progress ----
_EVAL = {"proc": None, "log": None}


def _debug_ok(request: Request):
    if PROD or os.getenv("ENABLE_DEBUG", "1") == "0" or (request.client and request.client.host not in ("127.0.0.1", "::1", "localhost")):
        raise HTTPException(404)


@app.post("/debug/eval/start")
def debug_eval_start(request: Request, label: str = "baseline", only: str = "", sleep: float = 3.0):
    _debug_ok(request)
    import re
    import subprocess
    import sys
    here0 = os.path.dirname(os.path.abspath(__file__))
    pf = os.path.join(here0, "..", "eval", "results", "last_run.pid")
    if (_EVAL["proc"] and _EVAL["proc"].poll() is None) or (os.path.exists(pf) and _pid_running_eval(int(open(pf).read().strip() or 0))):
        return {"started": False, "reason": "an eval is already running (POST /debug/eval/stop first)"}
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", label) or not re.fullmatch(r"[A-Za-z0-9,]*", only):
        raise HTTPException(400, "bad label or only")
    here = os.path.dirname(os.path.abspath(__file__))
    outdir = os.path.join(here, "..", "eval", "results")
    os.makedirs(outdir, exist_ok=True)
    logpath = os.path.join(outdir, "last_run.log")
    cmd = [sys.executable, os.path.join(here, "..", "eval", "run_eval.py"), "--label", label, "--sleep", str(sleep)]
    if only:
        cmd += ["--only", only]
    env = dict(os.environ, DATABASE_URL="sqlite:///" + os.path.join(here, "..", "eval", "eval_tmp.db"), PYTHONUNBUFFERED="1")
    _EVAL["log"] = open(logpath, "w")
    _EVAL["proc"] = subprocess.Popen(cmd, cwd=here, env=env, stdout=_EVAL["log"], stderr=subprocess.STDOUT)
    with open(os.path.join(outdir, "last_run.pid"), "w") as fh:
        fh.write(str(_EVAL["proc"].pid))
    return {"started": True, "pid": _EVAL["proc"].pid, "log": "eval/results/last_run.log"}


def _pid_running_eval(pid: int) -> bool:
    import subprocess
    try:
        out = subprocess.run(["ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return False
    return "run_eval.py" in out


@app.post("/debug/eval/stop")
def debug_eval_stop(request: Request, pid: int | None = None):
    """Stop a running eval (also one started before a server reload). Only ever signals a process whose command is run_eval.py."""
    _debug_ok(request)
    import signal
    here = os.path.dirname(os.path.abspath(__file__))
    pidfile = os.path.join(here, "..", "eval", "results", "last_run.pid")
    if pid is None:
        if not os.path.exists(pidfile):
            return {"stopped": False, "reason": "no eval recorded"}
        pid = int(open(pidfile).read().strip() or 0)
    if pid and _pid_running_eval(pid):
        os.kill(pid, signal.SIGTERM)
        return {"stopped": True, "pid": pid}
    return {"stopped": False, "reason": "not running"}


@app.get("/debug/eval/status")
def debug_eval_status(request: Request):
    _debug_ok(request)
    p = _EVAL["proc"]
    logpath = _EVAL["log"].name if _EVAL["log"] else None
    tail = ""
    if logpath and os.path.exists(logpath):
        with open(logpath, errors="replace") as fh:
            tail = fh.read()[-6000:]
    here = os.path.dirname(os.path.abspath(__file__))
    pidfile = os.path.join(here, "..", "eval", "results", "last_run.pid")
    running = bool(p and p.poll() is None)
    if not running and os.path.exists(pidfile):
        try:
            running = _pid_running_eval(int(open(pidfile).read().strip() or 0))
        except Exception:
            pass
    if not logpath:
        lp = os.path.join(here, "..", "eval", "results", "last_run.log")
        if os.path.exists(lp):
            with open(lp, errors="replace") as fh:
                tail = fh.read()[-6000:]
    return {"running": running, "exit_code": None if (not p or p.poll() is None) else p.poll(), "log_tail": tail}


# Production: serve the built UI from this same service (after every API route is registered).
_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist")
if os.path.isdir(_DIST):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="ui")
