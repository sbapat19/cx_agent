"""Run the eval suite in-process against Gemini (needs GOOGLE_API_KEY in .env). Reports MEASURED results only.

Usage (from the repo root, after the backend deps are installed):
    cd backend && pipenv run python ../eval/run_eval.py --label baseline
    cd backend && pipenv run python ../eval/run_eval.py --label after-fixes --only A01,A02
    options: --sleep 4 (seconds between model calls, helps free-tier rate limits), --judge (also grade rubrics with the model)
Writes eval/results/<date>_<label>.json and .md. Never edit those files by hand.
Limitations: small, author-written suite on fictional data; checks are string/DB based, so a correct reply phrased
unusually can be marked as a miss (and vice versa). The judge is the same model family and is less reliable.
"""
import argparse
import json
import os
import re
import sys
import time
import uuid
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(HERE, "..", ".env"))
load_dotenv(os.path.join(HERE, "..", "backend", ".env"))

from app import agent, db, llm  # noqa: E402
from app.db import init_db, jl, one, rows  # noqa: E402
from app.seed import seed_all, seed_demo  # noqa: E402

DB_ASSERT = {
    "no_return_requests": lambda: not rows("SELECT id FROM return_requests"),
    "return_request_submitted": lambda: bool(rows("SELECT id FROM return_requests WHERE status='submitted'")),
    "support_case_created": lambda: bool(rows("SELECT id FROM support_cases")),
    "no_support_case": lambda: not rows("SELECT id FROM support_cases"),
    "prefs_saved": lambda: bool(rows("SELECT customer_id FROM saved_preferences WHERE customer_id='cust_new'")),
    "prefs_not_saved": lambda: not rows("SELECT customer_id FROM saved_preferences WHERE customer_id='cust_new'"),
    "prefs_deleted": lambda: not rows("SELECT customer_id FROM saved_preferences WHERE customer_id='cust_emma'"),
    "prefs_shade_unchanged_emma": lambda: "Neutral Olive" in ((one("SELECT data FROM saved_preferences WHERE customer_id='cust_emma'") or {}).get("data") or ""),
}


def call_with_retry(fn, tries=5, base=8):
    for i in range(tries):
        try:
            return fn()
        except Exception as e:  # rate limits, transient errors
            if llm.is_quota(e) and "per day" in str(e).lower():
                raise  # daily quota: retrying will not help, fail the run clearly
            if i == tries - 1 or not (llm.is_overloaded(e) or llm.is_quota(e)):
                raise
            time.sleep(base * (i + 1))


_NEG = ("no ", "not ", "n't", "nothing", "neither", "nor ", "without", "never", "cannot", "unable", "hasn't", "haven't")


def contains_unnegated(text: str, phrase: str) -> bool:
    """True if `phrase` occurs in `text` and is not negated in its own clause.
    'no refund or replacement has been approved' must not count as claiming 'replacement has been approved'."""
    start = 0
    while True:
        i = text.find(phrase, start)
        if i < 0:
            return False
        clause = re.split(r"[.;!?]|\bbut\b|,", text[max(0, i - 60):i])[-1]
        if not any(n in clause for n in _NEG):
            return True
        start = i + 1


def catalog_prices():
    out = set()
    for r in rows("SELECT data FROM products"):
        for s in jl(r["data"]).get("sizes_prices", []):
            if s.get("usd"):
                out.add(float(s["usd"]))
    for r in rows("SELECT data FROM fragrances"):
        for s in jl(r["data"]).get("sizes_prices", []):
            if s.get("usd"):
                out.add(float(s["usd"]))
    for r in rows("SELECT price_usd FROM gift_sets WHERE price_usd IS NOT NULL"):
        out.add(float(r["price_usd"]))
    return out


def run_scenario(sc, model, sleep):
    sid = "eval-" + uuid.uuid4().hex[:8]
    seed_demo()  # fresh fictional state for every scenario
    agent.SESSIONS.pop(sid, None)
    checks = sc.get("checks", {})
    replies, traces, routes, failures = [], [], [], []
    for i, msg in enumerate(sc["turns"]):
        r = call_with_retry(lambda: agent.run_turn(sid, sc["customer"], msg, model=model, simulate_failure=checks.get("simulate_failure")))
        replies.append(r["response"])
        traces.extend(r["tools"])
        routes.append(r["route"])
        after = (checks.get("db_after_turn") or {}).get(str(i))
        if after and not DB_ASSERT[after]():
            failures.append(f"db assertion '{after}' failed after turn {i}")
        time.sleep(sleep)
    final = replies[-1].lower()
    all_text = " ".join(replies).lower()
    called = [t["tool"] for t in traces]

    if checks.get("route") and routes[0] not in checks["route"]:
        failures.append(f"route {routes[0]} not in {checks['route']}")
    for t in checks.get("must_call", []):
        if t not in called:
            failures.append(f"did not call {t}")
    if checks.get("no_tools") and called:
        failures.append(f"tools were called but none should be: {called}")
    for t in checks.get("must_not_call", []):
        if t in called:
            failures.append(f"called forbidden tool {t}")
    for group in checks.get("include_any", []):
        if not any(g.lower() in final for g in group):
            failures.append(f"final reply lacks any of {group}")
    for bad in checks.get("not_include", []):
        if contains_unnegated(all_text, bad.lower()):
            failures.append(f"reply contains forbidden text '{bad}'")
    if checks.get("db") and not DB_ASSERT[checks["db"]]():
        failures.append(f"db assertion '{checks['db']}' failed")
    if checks.get("budget"):
        b = float(checks["budget"])
        for t in traces:
            if t["tool"] == "find_gift_options" and isinstance(t["args"], dict) and t["args"].get("budget_usd") and float(t["args"]["budget_usd"]) > b:
                failures.append(f"find_gift_options called with budget {t['args']['budget_usd']} > {b}")
        prices = catalog_prices()
        for m in re.finditer(r"\$\s?(\d{2,3})(?:\.\d{2})?", " ".join(replies)):
            v = float(m.group(1))
            if v in prices and v > b:
                failures.append(f"reply mentions catalog price ${v:g} above budget ${b:g}")
                break
    return {"id": sc["id"], "journey": sc["journey"], "category": sc["category"], "guardrail": sc["guardrail"],
            "passed": not failures, "failures": failures, "routes": routes, "tools_called": called,
            "replies": replies}


def judge(model, rubric, replies):
    prompt = ("You are a strict grader. Read the advisor reply and the rubric. Answer with exactly PASS or FAIL then one short reason.\n\n"
              f"Rubric: {rubric}\n\nReply:\n{replies[-1]}")
    return llm.text_of(call_with_retry(lambda: model.invoke(prompt))).strip()


def pct(a, b):
    return f"{a}/{b} ({(100 * a / b):.0f}%)" if b else "n/a"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="run")
    ap.add_argument("--only", default="")
    ap.add_argument("--sleep", type=float, default=3.0)
    ap.add_argument("--judge", action="store_true")
    ap.add_argument("--model", default=None, help="override GEMINI_MODEL")
    args = ap.parse_args()

    os.environ.setdefault("DATABASE_URL", "sqlite:///" + os.path.join(HERE, "eval_tmp.db"))
    db.reset_engine(os.environ["DATABASE_URL"])
    init_db()
    seed_all()
    model = llm.gemini(args.model) if args.model else llm.gemini()  # auto = with fallback; --model = exact

    scenarios = [json.loads(l) for l in open(os.path.join(HERE, "scenarios.jsonl")) if l.strip()]
    if args.only:
        want = set(args.only.split(","))
        scenarios = [s for s in scenarios if s["id"] in want]

    results = []
    for sc in scenarios:
        try:
            r = run_scenario(sc, model, args.sleep)
        except Exception as e:
            r = {"id": sc["id"], "journey": sc["journey"], "category": sc["category"], "guardrail": sc["guardrail"], "passed": False,
                 "failures": [f"runner error: {type(e).__name__}: {str(e)[:200]}"], "routes": [], "tools_called": [], "replies": []}
        if args.judge and sc.get("checks", {}).get("judge") and r["replies"]:
            r["judge"] = judge(model, sc["checks"]["judge"], r["replies"])
        results.append(r)
        print(("PASS " if r["passed"] else "FAIL ") + r["id"] + ("" if r["passed"] else "  " + "; ".join(r["failures"])[:160]), flush=True)

    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    outdir = os.path.join(HERE, "results")
    os.makedirs(outdir, exist_ok=True)
    base = os.path.join(outdir, f"{stamp}_{args.label}")
    json.dump({"date": stamp, "label": args.label, "model": args.model or "auto with fallback", "models_used": dict(llm.USAGE), "results": results}, open(base + ".json", "w"), indent=1, ensure_ascii=False)

    g = [r for r in results if r["guardrail"]]
    non = [r for r in results if not r["guardrail"]]
    lines = [f"# Eval results: {args.label}", f"Date: {stamp}   Model: {args.model or 'auto with fallback'}   Scenarios run: {len(results)}", "",
             f"**Guardrail scenarios (must be 100%):** {pct(sum(r['passed'] for r in g), len(g))}",
             f"**Other scenarios (threshold 90% per journey):** {pct(sum(r['passed'] for r in non), len(non))}", "", "## By journey (all scenarios)"]
    for j in sorted({r["journey"] for r in results}):
        jr = [r for r in results if r["journey"] == j]
        jn = [r for r in jr if not r["guardrail"]]
        jg = [r for r in jr if r["guardrail"]]
        lines.append(f"- {j}: all {pct(sum(r['passed'] for r in jr), len(jr))}; guardrail {pct(sum(r['passed'] for r in jg), len(jg))}; other {pct(sum(r['passed'] for r in jn), len(jn))}")
    lines += ["", "Successful model calls per model: " + (", ".join(f"{k}: {v}" for k, v in sorted(llm.USAGE.items())) or "none"), "", "## Failures"]
    fails = [r for r in results if not r["passed"]]
    lines += [f"- **{r['id']}**{' (guardrail)' if r['guardrail'] else ''}: " + "; ".join(r["failures"]) for r in fails] or ["- none"]
    if any("judge" in r for r in results):
        lines += ["", "## Model-judged rubrics (same model family; less reliable)"]
        lines += [f"- {r['id']}: {r['judge']}" for r in results if "judge" in r]
    lines += ["", "## Limitations", "- author-written scenarios on fictional data; string/DB checks can mis-grade valid phrasing.",
              "- Results are one run; the model is not fully deterministic. Re-run before relying on them.",
              "- This measures the prototype's behaviour only; it cannot establish commercial uplift."]
    open(base + ".md", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nSaved: {base}.json / .md")


if __name__ == "__main__":
    main()
