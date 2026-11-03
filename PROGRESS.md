# PROGRESS

Last updated: 2026-11-02.

## Done
- Phase 1 docs: `docs/audit_and_plan.md`, `docs/deploy_requirements.md`, `docs/source_access.md` (see data_verification.md for the current data status).
- Verified data captured and loaded: 11 products, 9 fragrances, 17 gift sets, 9 policy topics, 17 New York stockists; fictional customers/orders (6 customers, 7 orders).
- Tool layer with code-enforced scoping, eligibility, confirmation and consent (`backend/app/tools.py`); 27 deterministic tests.
- Router + 6 specialists (LangGraph), Gemini model layer with auto-selection of an available model (the hard-coded gemini-2.5-flash was retired for the owner's key: 404), FastAPI, session binding; plumbing tests with a scripted model.
- Polite fixed refusal for abusive/nonsense/manipulative messages (BLOCK) and human handoff for relevant-but-out-of-scope requests (HANDOFF), both tested. UI message box is now a multi-line text area (Enter sends), always editable.
- Frontend (scenario buttons, chat, show-your-work panel, preferences view, disclaimer); production build verified; UI screenshot checked against a stand-in model.
- Eval suite: 55 scenarios (37 guardrail), runner with dated results. Checks tightened after a refusal-only dummy bot passed 18/48; on the 55 it passes 2/55 (both legitimate out-of-scope/clarify cases).

## Findings from testing the live app on the owner's Mac (2026-11-02)
- The owner's Gemini key is on the **free tier: 20 requests per model per day** (Google 429 message). One chat turn makes 3-8 model calls, so the free tier allows only a few conversations per day, and the full eval (~55 scenarios, hundreds of calls) cannot complete on it. A baseline eval was started and stopped when the quota ran out; **no results were saved and no baseline exists yet.**
- Fixed during testing: retired default model (404); macOS SSL certificate error on the model lookup; newest models returning 503 (automatic fallback + cooldown); a fallback that wrongly reached a transcription model; `create_support_case` required an order id (non-order handoffs failed); gift search looped until the step limit (now forces a real final answer and stops returning makeup for men's fragrance gifts); replies showed raw markdown (now rendered); "will contact you with a resolution" over-promise (prompt tightened).
- Verified by typing in the live app: damaged order -> options -> support case (CASE id, "not resolved"); rude message -> polite fixed refusal; loyalty question -> human handoff case; foundation request -> candidate shades + uncertainty + official link.
- Not yet re-verified live after the last fixes: gift flow, returning customer, other-customer isolation, counter finder (blocked by the quota).

## Eval history (measured, `gemini-3.1-flash-lite`)
baseline 22/37 guardrail, 16/18 other -> after-fixes 35/37, 17/18 -> run3 36/37, 18/18 -> final-run1 37/37, 18/18 -> final-run2 37/37, 18/18 (repeat, same code). After the persona change (suite now 56): 34/37 -> 35/38 -> 36/38 -> friendly-run4 38/38, 18/18. Final pre-deploy full run (57 scenarios): 34/38 guardrail, 18/19 other; fixes verified on the 5 affected scenarios only (5/5), no full re-run since. Details and every check change: `docs/eval_changes.md`.

## Not done / next
1. Deploy (needs approval and accounts in `docs/deploy_requirements.md`; set `ENABLE_DEBUG=0`; run the schema on Postgres once; consider pinning `GEMINI_MODEL`).
2. Recorded fallback demo video.
3. Optional data: more products/fragrances; set contents for the remaining gift sets.
4. Evaluate a second model for comparison; extend the suite beyond 55 author-written scenarios.

## (older notes, kept for history)
### Earlier next-steps list
1. **Get quota for the Gemini key (enable billing on its Google project, or wait for the daily reset and run in parts), then run the baseline eval** (`cd backend && pipenv run python ../eval/run_eval.py --label baseline --sleep 3`). Record results in `eval/results/` as-is. Estimated 300-500 model calls per full run (unverified estimate).
2. Fix failures, up to 3 attempts per failing guardrail case, then log here and move on.
3. Deploy (needs approvals and accounts in `docs/deploy_requirements.md`); run the schema on Postgres once; recorded fallback demo video.
4. Optional data: more products/fragrances; fuller shade lists for Power Fabric+ and the Skin Tint undertones; set contents for the remaining gift sets.

## Decisions
- Local DB is SQLite for easy testing; Postgres at deploy via `DATABASE_URL`.
- Return window measured from the order (transaction) date, per "within 30 days of the transaction".
- Damaged/wrong/missing items never get an automatic remedy: standard return (if in window) or human support case.
- Memory: two-step propose/confirm gated on a later user turn (code-enforced); this guards against same-turn self-confirmation but cannot verify the customer's reply was an actual "yes"; the model judges that.
- The old Bloom agent, router eval and result are kept in `legacy_bloom/`, not deleted.

## Open problems / known risks
- Nothing has run against Gemini yet. Behavior with the real model (tool-call formatting, history replay of tool messages, refusal phrasing vs the string checks) is unmeasured.
- `confirm_save_preferences` relies on the model to only call it after a real yes.
- Data staleness (prices, promos, stock).
