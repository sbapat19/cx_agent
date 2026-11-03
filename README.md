# Independent beauty advisor prototype

**Independent work sample. Not affiliated with Armani Beauty, L'Oréal or Sierra.** Public information only. All customers, orders, returns and support cases are **fictional**, and every transaction is **simulated**. This is a reliable prototype, not a production commerce platform.

An AI advisor for a luxury beauty brand's direct website: order problems, foundation advice, a returning-customer experience with consent-based memory, gift buying for someone else, and a minimal counter finder. Business case and pilot are in the separate Strategy Brief.

## Status (read this first)

| Item | State |
|---|---|
| Backend, tools, database, UI | Built and tested live by typing in the running app |
| Deterministic tests (`backend/tests`, no model, no network) | **85 pass** |
| Eval suite (`eval/scenarios.jsonl`, 56 scenarios, 38 guardrail) | Run against Gemini on 2026-11-02 with `gemini-3.1-flash-lite`. See "Measured eval results" below; dated files are in `eval/results/` |
| Live deploy | Not done (see `docs/deploy_requirements.md`) |

### Measured eval results (all on `gemini-3.1-flash-lite`, one run each, same 55 scenarios)

| Run | Guardrail (must be 100%) | Other (must be 90%+) | Notes |
|---|---|---|---|
| `2026-11-02_1324_baseline` | 22/37 (59%) | 16/18 (89%) | before any fix; kept unedited |
| `2026-11-02_1331_after-fixes` | 35/37 (95%) | 17/18 (94%) | agent fixes plus corrected checks |
| `2026-11-02_1337_run3` | 36/37 (97%) | 18/18 (100%) | |
| `2026-11-02_1342_final-run1` | 37/37 (100%) | 18/18 (100%) | after the last fix |
| `2026-11-02_1348_final-run2` | 37/37 (100%) | 18/18 (100%) | same code, repeat run (non-deterministic model; two clean runs in a row is not a guarantee) |
| `2026-11-02_1415_friendly-persona` | 34/37 (92%) | 18/18 (100%) | after the friendlier persona + finder link: model invented a finder URL (fixed in code); 2 phrasing-only failures |
| `2026-11-02_1422_friendly-run2` | 35/38 (92%) | 18/18 (100%) | suite now 56 scenarios; 1 real quality issue (B09), 2 phrasing |
| `2026-11-02_1430_friendly-run3` | 36/38 (95%) | 18/18 (100%) | B09 was being routed to a human handoff |
| `2026-11-02_1438_friendly-run4` | 38/38 (100%) | 18/18 (100%) | 56 scenarios; one run, so not a guarantee |
| `2026-11-02_pre-deploy` | 34/38 (89%) | 18/19 (95%) | 57 scenarios, after the later tone, flow and brevity changes: 3 phrasing-only failures, 2 real regressions (counter list dropped; shade lookup skipped). Fixed; the 5 affected scenarios then passed 5/5 in a targeted re-run (`pre-deploy-fixes`). A full re-run after those fixes has NOT been done, so there is no clean full-suite number for the final code. |

Every change between runs, including which checks were corrected because they marked right answers wrong, is in `docs/eval_changes.md`. The model is not fully deterministic, so a single run can differ from the next; see the later runs in `eval/results/` for stability. Re-run before relying on a number.

**A live demo needs a Gemini key with billing enabled.** The free tier (about 20 requests per model per day) was exhausted during testing; with billing on, a full 55-scenario eval ran in about 5 minutes. Set `GEMINI_PREFERRED=gemini-3.1-flash-lite` (cheapest model that worked on the owner's key; prices are from third-party pages, confirm in AI Studio).

## Run it locally (about 5 minutes)

Requirements: Python 3 with `pipenv`, Node 18+, and a Gemini key in `.env`.

```bash
cd ~/cx_agent
cp -n .env.example .env        # if you have no .env yet; add GOOGLE_API_KEY=...
./run_local.sh                  # backend on :8000, frontend on :5173
# open http://localhost:5173
```

1. First check your key: `cd backend && pipenv run python scripts/check_gemini.py`. It lists the models your key can call and shows which one the app will pick. By default the app asks Google which models your key can use and picks the newest stable flash model; if a model is retired it skips it and retries once. To force one, set `GEMINI_MODEL=<name>` in `.env` (an explicit setting is never silently swapped).
2. Click a scenario button on the left, or type your own message in the box at the bottom (Enter sends, Shift+Enter adds a line). Click any reply to see the **Show your work** panel: route, tool calls with arguments and results, policies retrieved, escalation.
3. No key yet? `cd backend && pipenv run python scripts/dev_fake_server.py` serves a stand-in model that only handles the damaged-order scenario, so you can check the UI. It is not the real advisor.

## Run the tests and evals

```bash
cd backend && pipenv run pytest tests -q                       # deterministic guardrail tests (no model, no network)
cd backend && pipenv run python ../eval/run_eval.py --label baseline --sleep 4   # 55 scenarios against Gemini; writes eval/results/
```

Add `--judge` to also grade a few rubric items with the model (reported separately; less reliable). Use `--only A01,A02` to rerun failures. Fix, re-run, and keep every dated results file.

Pass thresholds (spec): **100%** on guardrail scenarios; **at least 90%** on the rest per journey. A journey that misses ships labelled known-limited. Do not loosen a check to raise a score.

## Architecture

```
React UI (scenario buttons, chat, "show your work", saved-preferences view)
   | POST /chat {customer_id, session_id, message}
FastAPI (main.py)  ->  LangGraph (app/agent.py): router -> specialist agent (tool loop, max 8 steps)
   specialists: ORDER_ISSUE, PRODUCT_ADVICE, RETURNING, GIFT, COUNTER, HANDOFF, NEEDS_CLARIFICATION
   fixed replies (no model-written text): BLOCK (abuse, gibberish, jailbreaks), OUT_OF_SCOPE (unrelated)
   Gemini via langchain-google-genai (app/llm.py)
Tools (app/tools.py)  <- identity, permissions and policy logic enforced here, in code
SQL database (app/db.py): SQLite locally, Postgres via DATABASE_URL
```

Rules enforced in code, not in prompts (each has a test):
- A tool can only touch the **signed-in customer's** records; the customer id comes from the session, never from the model. A request for someone else's order gets the same answer as a nonexistent order.
- **Return eligibility** is computed from stored policy facts (30-day window, final-sale/engraved/promo exclusions, delivered status). The policy text names **no automatic remedy for damaged/wrong/missing items**, so those go to a human support case; the model cannot override it.
- Actions need an **eligibility check and a later user turn** (confirmation). A return request reports `submitted`, never `completed`; a support case is `open_awaiting_human_review`, never resolved.
- **Memory is consent-based:** propose, then confirm on a later turn. Only the customer's own preferences can be stored; text about a gift recipient is rejected. Customers can view and delete.
- **Prompt injection:** order notes and other free text are returned as `..._UNTRUSTED_TEXT` with a warning; one fictional order contains an injected "approve a refund" note to test this.
- **Rude, nonsense or manipulative messages** get a polite, fixed (code-written, not model-written) refusal that cannot be argued with; it gets firmer but stays polite on repeats and never ends the chat. Frustration about a real problem is not blocked: it is handled as the real problem.
- **Relevant but out of scope** (account/payment changes, loyalty details, skincare advice, a possible reaction to a product, etc.) is handed to a human: a support case is opened for a signed-in customer (reported as submitted, not resolved); otherwise the verified contact options are given. The handoff specialist cannot grant returns or answer the question from general knowledge.
- Each specialist only gets the tools for its journey. Tool failures are caught and reported honestly.

## Data model

Verified catalog (every row has `source_url` and `last_verified`; `status` = verified or partial; missing fields are null): `products`, `fragrances`, `gift_sets`, `policies`, `counters`. Fictional/simulated: `customers`, `orders`, `support_cases`, `return_requests`, `saved_preferences`, `sessions`, `messages`.

## How the data was verified

- Captured 2026-11-02 from the official US beauty site (`giorgioarmanibeauty-usa.com`). Returns/shipping policy, the Luminous Silk foundation (all 44 shades), four fragrances and gift-set listings were read directly in a browser pane. A larger set (11 products, 9 fragrances, gift sets, a New York store list) came from pages the project owner pasted in; overlapping fields were spot-checked against the direct reads and matched. Details: `docs/data_verification.md`.
- Nothing is filled in from memory or third-party sites. Policy text keeps the page's ambiguities (for example an "$8.00 deduction" and a separate "original shipping not refunded" statement; whether holiday sets count as "promotional gift items").
- Prices, promotions and stock are as shown on the capture date and **will go stale**.

## Known limitations

- The suite is small, author-written, on fictional data; checks are string/DB based. About a dozen correct replies were wrongly flagged in the first runs and the checks were corrected (see `docs/eval_changes.md`), so treat 100% as 'passes these 55 checks', not as proof of correctness. Only one model (`gemini-3.1-flash-lite`) has been evaluated.
- Fragrance pages publish a description and "key notes", not a top/heart/base pyramid (only Armani Code has one). The advisor quotes notes as published and does not invent layers. Sì's description and key-notes line disagree; both are quoted.
- Gift-set contents are known for 5 sets only; for others the advisor must say contents are not captured.
- Shade matching from a text description is approximate by design; there is no verified mapping from older shade numbers.
- Counter finder covers a curated New York list from the official locator (addresses only; it does not say which locations have a beauty counter). Elsewhere it points to the official locator.
- Session history is held in server memory (it is lost on restart); preferences, orders and cases persist in the database. Demo "sign-in" is a selector of fictional customers, not real authentication.
- Locally the database is SQLite. Deployment uses Postgres (`DATABASE_URL`); the schema uses only portable SQL but has not been run on Postgres yet.
- This prototype can demonstrate capability and journeys. It **cannot** establish commercial uplift.

## Deploy

See `docs/deploy_requirements.md`. Not deployed yet.

## Local debug endpoints (localhost only)

`/debug/stage/{db,list,init,ping,tools}`, `/debug/timings`, and `/debug/eval/{start,status,stop}` are for development: they time model calls and run the eval in a separate process. They return 404 from any other host and are disabled with `ENABLE_DEBUG=0`. **Set `ENABLE_DEBUG=0` when deploying.** They never return the API key.
