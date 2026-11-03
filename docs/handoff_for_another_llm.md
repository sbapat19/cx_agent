# Handoff: deploy and maintain the Beauty Assistant prototype

You are taking over an existing project. Read this fully before acting. Do the deployment steps in order, and stop and ask the owner (Shalaka) at every point marked STOP.

## 1. What this project is
An AI beauty-advisor chat prototype inspired by a luxury beauty brand's website. It is INDEPENDENT: not affiliated with Armani Beauty, L'Oreal or Sierra. All customers, orders, returns and support cases are FICTIONAL and SIMULATED. Product and policy facts come from public brand pages captured 2026-11-02 and may have changed. Never remove the footer disclaimer. Do not add brand logos, photos or other brand assets. The public page title is "Beauty Assistant" (build arg `VITE_BRAND_TITLE`); do not change it to a brand name for the public site.

- Repo: https://github.com/sbapat19/cx_agent , branch `armani-advisor` (latest commits include a `Dockerfile` and `render.yaml`).
- Stack: FastAPI + SQLAlchemy backend (`backend/`), React/Vite UI (`frontend/`), LangGraph router with specialist workflows, Gemini via `langchain-google-genai`. SQLite by default; Postgres if `DATABASE_URL` is set.
- Production mode (`APP_ENV=production`, set by the Dockerfile) serves the built UI and API from one service, turns OFF `/debug/*` and `/demo/reset`, and turns ON abuse limits.

## 2. Architecture in brief (do not restructure without being asked)
- One router LLM call classifies each message into: ORDER_ISSUE, PRODUCT_ADVICE, RETURNING, GIFT, COUNTER, HANDOFF, NEEDS_CLARIFICATION, BLOCK, OUT_OF_SCOPE.
- Specialist nodes run a tool loop (max 8 steps) with a restricted tool set per intent. BLOCK and OUT_OF_SCOPE return fixed replies.
- Guardrails are enforced in CODE, not only prompts: customer scoping from the session, return eligibility, a verifier that rejects invented case/return IDs, consent-gated memory, a safety notice for possible reactions, and the single official Foundation Finder link appended by code.
- Main files: `backend/app/agent.py` (prompts, graph, verifier), `backend/app/tools.py` (tools), `backend/app/catalog_data.py` (verified catalog), `backend/main.py` (API, limits), `frontend/src/App.jsx`, `eval/` (scenarios and runner), `docs/eval_changes.md` (every eval change).

## 3. Hard rules for you
1. NEVER print, log, commit or paste the Gemini API key or any secret. It goes only in the host's environment settings.
2. NEVER bypass CAPTCHAs or bot protection, create accounts, or enter passwords or payment details for the owner. If a page needs these, STOP and tell the owner exactly what to click.
3. No invented product, price, policy or promotion data. Unknown fields stay null. If you add catalog data, include `source_url` and `last_verified`.
4. Do not weaken guardrails, and do not loosen an eval check to raise a score. Any change to a check must be logged in `docs/eval_changes.md` with the reason.
5. Report eval numbers exactly as measured, including failures. Do not claim a full-suite pass unless a full run just completed.
6. Do not run full evals repeatedly (about 9 minutes and paid Gemini calls each). The owner has asked to limit them. Run targeted scenarios (`only=ID1,ID2`) while iterating and at most one full run at the end.
7. STOP and ask before: changing the LLM provider, adding paid services beyond the host plan, or making any change that spends money.

## 4. Deployment steps (Render, Docker, SQLite)
The owner has not yet deployed. Hosting recommendation: Render, "Starter" plan (about $7/month). The free tier sleeps and is slow on the first message.

STOP at step 1 if you cannot do it; the owner must do the logins.
1. The owner pushes the branch: `git push -u origin armani-advisor` (needs their GitHub login).
2. On render.com: New > Blueprint > select `sbapat19/cx_agent`, branch `armani-advisor`. It reads `render.yaml` (Docker web service named `beauty-assistant`, health check `/health`, `APP_ENV=production`).
3. When asked for `GOOGLE_API_KEY`, the owner pastes a Gemini key (their choice: reuse the existing key or make a new one; a separate key for the public site is optional but gives independent control). Then Apply.
4. Wait for the build (several minutes). Render gives a public URL.
5. Set a budget alert or spending cap on the Google Cloud project behind the key (recommended; the owner does this).

Optional settings (Render > Environment): `RATE_LIMIT_MESSAGES` (default 20 per IP per 10 min), `RATE_LIMIT_WINDOW_SECONDS` (600), `DAILY_MESSAGE_CAP` (default 1500 total per day), `MAX_MESSAGE_CHARS` (1000), `GEMINI_MODEL` (leave unset to auto-pick), `DATABASE_URL` (only if using Postgres; not needed for a demo).

## 5. Verify the live site (all must pass)
Replace `$URL` with the public address.
- `GET $URL/health` returns `{"status":"ok", ... "gemini_key_set": true}`.
- `GET $URL/` shows the chat page with the footer disclaimer and the title "Beauty Assistant".
- `GET $URL/debug/timings` and `POST $URL/demo/reset` both return 404.
- `GET $URL/api/customers` returns the fictional customers.
- In the browser, as a guest: tap "Pick my foundation shade". The reply asks about coverage first, with one short question. After answering, it asks about skin tone/undertone and includes the Foundation Finder link once.
- Tap "Help with an order", sign in as a demo customer (e.g. Ava Laurent), and ask about order ORD-1001 being damaged. A support case with a `CASE-` id should be created and described as "not resolved".
- Send 21 messages quickly from one browser; a friendly rate-limit message should appear.

## 6. If something fails
- Build error: read the Render build log; the Dockerfile has a Node stage (builds the UI) and a Python stage. Fix, commit, push.
- "GOOGLE_API_KEY not set" (503): the env var is missing or misnamed on Render.
- 429 "quota" from the model: free-tier limits or billing not enabled on the Google project. The owner must enable billing (do not do this for them).
- 502 model errors: newer Gemini models are sometimes overloaded; the app falls back automatically between chat models (cooldowns). Wait and retry; check `/health`.
- Chats reset after a redeploy or restart: expected (sessions are in memory; SQLite is on ephemeral disk).

## 7. Local development
- Backend: `cd backend && pipenv install --dev && pipenv run uvicorn main:app --reload --port 8000`. Frontend: `cd frontend && npm install && npm run dev` (port 5173; `/api` is proxied).
- `.env` (never committed): `GOOGLE_API_KEY=...`; optional `GEMINI_MODEL`, `GEMINI_PREFERRED`.
- Tests: `cd backend && python -m pytest -q` (89 should pass; no network or LLM needed).
- Evals: `eval/run_eval.py` (in-process); results in `eval/results/<date>_<label>.json/.md`. Scenarios are generated by `eval/build_scenarios.py` into `eval/scenarios.jsonl` (57 scenarios, 38 guardrail). Pass thresholds: 100% guardrail, 90%+ others.
- Git note on the owner's Mac: git run through the sandbox can leave `.lock` files under `.git` that cannot be deleted. Move them aside (`mv .git/HEAD.lock .git/stale-HEAD-lock-N`) rather than deleting.

## 8. Current state and known limits (be honest about these)
- Last full eval ("pre-deploy", 57 scenarios): 34/38 guardrail, 18/19 other. Three failures were phrasing-only (checks widened and logged), two were real regressions (store finder dropped its stockist list; shade lookup skipped when the customer gave skin tone). Both were fixed and the 5 affected scenarios then passed 5/5 in a targeted run. There has been NO full re-run since, so there is no clean full-suite number for the final code.
- Only one model (`gemini-3.1-flash-lite`) was evaluated; the model is non-deterministic. Scenarios were written by the project author on fictional data.
- The catalog covers makeup (11 products) and fragrance (9) plus some gift sets and 17 NYC stockists. It has NO skincare data (the brand does sell skincare); skincare questions are handed to a human with an honest message. Some prices, fragrance details and gift-set contents are unpublished and left empty.
- Design choices by the owner: the assistant speaks AS the brand ("we", "our"), is brief (2 to 4 sentences, one question per turn), does not volunteer prices or return policy in recommendations, asks about coverage FIRST for foundation, then skin tone/undertone, and offers the Foundation Finder link once per conversation (never after the customer gives a shade).
- An order number not on the signed-in account is accepted as customer-reported and UNVERIFIED in a support case; it never reveals or links to another customer's order.

## 9. What to report back to the owner
The public URL, the result of each check in section 5 (pass or fail with the evidence), anything you changed (with commit hashes), and anything you could not do and why.
