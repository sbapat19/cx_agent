# Audit and plan (Phase 1, awaiting approval)

Independent work sample. Not affiliated with Armani Beauty, L'Oréal, or Sierra. Fictional customers, simulated transactions.

## 1. BloomBot audit: reuse vs. change

Confirmed by reading `backend/agent.py`, `eval/results.txt`, and the file tree. Matches the spec's audit.

| Piece | Decision | Why |
|---|---|---|
| Router-then-specialist LangGraph pattern | **Keep**, as the top-level intent layer | Works; easy to show in the UI |
| FastAPI shell, `/health`, React skeleton, `start.sh` | **Keep, extend** | Fine as a base |
| JSONL eval harness | **Keep, extend** to ~40 scenarios | Spec requires extending, not replacing |
| Specialists (single LLM call each) | **Replace** with tool-using agents with session state | No tools, no state today |
| Bloom prompts and policy ("5-7 business days", store credit for opened items) | **Remove entirely** | Bloom Supplements policy. Must not carry to Armani |
| Hardcoded `confidence` | **Remove**, replace with real signals (tool results, policy citations, eval pass/fail) | It is a constant per route today |
| `OPENAI_API_KEY` / `ChatOpenAI` | **Change** to Gemini (your decision) | Needs your approval to confirm model choice, see section 4 |
| CORS `*` | **Replace** with the real frontend origin | Spec requirement |
| `backend/app/` (empty) | **Use** for tools, db, policy retrieval, memory | |
| Router classes | **Rework**: REFUND/REPLACEMENT/STORE_CREDIT become ORDER_ISSUE, PRODUCT_ADVICE, GIFT, ACCOUNT_PREFERENCES, COUNTER_FINDER, OUT_OF_SCOPE, NEEDS_CLARIFICATION. Order status and "never received" route to ORDER_ISSUE (fixes E07/E10) | Baseline: 16/20 (80%), misroutes E07, E10, E18, E19 |

Nothing is removed without telling you; the Bloom prompts are the only removal planned, and they are replaced, not salvaged.

## 2. Target architecture

```
React UI (scenario buttons, chat, "show your work" panel)
   |  POST /chat {session_id, customer_id, message}
FastAPI
   |-- session store (Postgres): message history per session
   |-- LangGraph: router -> specialist agent (tool loop, max N steps)
   |        specialists: order_service, product_advisor, returning_customer, gift_advisor, counter_finder
   |-- tools (code-enforced customer scoping)
   |-- trace recorder -> returned with each reply for the UI panel
Postgres: products, fragrances, policies, counters (verified, with source_url + last_verified)
          fictional customers, orders, support cases, return requests, saved preferences
```

Key rules enforced in code, not prompts:
- Every order/preference tool takes `customer_id` from the authenticated session, never from model arguments. A tool cannot read another customer's order.
- `create_return_request` runs eligibility in code against stored policy and refuses if ineligible. The model cannot override.
- Tools return a status; the reply layer must report `submitted` vs. `completed` from that status.
- Saving preferences requires an explicit `consent=true` set only after the customer's confirming turn.
- Prompt-injection text inside order notes or product fields is passed as quoted data and never as instructions; tested in evals.

## 3. Data model (Postgres)

- `products` (id, name, category, collection, description, formulation, coverage, finish, texture, sizes, application, official_url, price, source_url, last_verified, status verified|partial)
- `shades` (product_id, name, code, undertone, depth, source_url)
- `fragrances` (id, name, concentration, scent_family, top_notes, heart_notes, base_notes, official_url, source_url, last_verified, status)
- `policies` (id, topic, text, source_url, last_verified, status)
- `counters` (id, name, city, state, zip, type, source_url, last_verified)
- FICTIONAL: `customers`, `orders`, `order_items`, `support_cases`, `return_requests`, `saved_preferences`, `sessions`, `messages`. Each table prefixed or flagged `fictional` and labelled in the UI.

## 4. LLM choice and cost

Gemini, per your decision. **I could not read Google's pricing page directly** (not on my fetch allowlist), so the numbers below come from third-party summaries that disagree on model lineup. Treat as **unverified until you confirm in Google AI Studio**.

- Third-party figures: a Flash-Lite class model at roughly $0.10-$0.30 per 1M input tokens and $0.40-$2.50 per 1M output; a Flash class model about $0.30-$0.75 input and $2.50-$3.75 output. Free tier exists with lower rate limits, and free-tier prompts may be used by Google to improve products.
- Estimated demo session (my assumption, not measured): ~15 model calls x ~3k input / ~400 output tokens = ~45k in / ~6k out. At the highest figures above that is well under $0.05 per session. At that rate $10 would not be limiting for LLM cost; hosting is.
- Plan: baseline eval on a Flash-Lite model first, then a Flash model if guardrail cases miss. Report both. Final model ID chosen from what AI Studio lists for your key.
- The free tier is fine for building. A live demo with several interviewers risks rate limits (reported as ~15-30 requests/minute for older free models, unconfirmed). Option: enable paid tier with a low spend cap. That needs a card, so I will ask first.

## 5. Hosting recommendation (needs your approval) and $10 reality check

Recommendation: **Render** (web service for FastAPI, static site for React, Postgres), because git push deploys and it is simple for a FastAPI + React app. Verified from Render's own docs and articles:
- Free web services spin down after 15 minutes idle; restart takes roughly 30-60 seconds. That fails your cold-start rule.
- Free Render Postgres expires 30 days after creation.
- Starter web service is $7/month and stays on. Smallest paid Postgres is reported around $6-7/month (Render's own article cites ~$13/month for Starter plus the smallest Postgres, as of July 2026). **That is already above your $10 cap before any LLM spend.**

Options within or near $10:
1. **Starter web service ($7) + a free-tier Postgres from another provider** (e.g. Neon or Supabase; I have not verified their current limits). Roughly $7/month plus tiny LLM cost. Stays under $10 for one month, then you decide.
2. **Free Render web service + keep-warm pinger** (a free uptime monitor hitting `/health` every ~10 minutes). $0, but Render says free services can be restarted at any time, so a cold start can still happen. Weaker for a live interview.
3. **Render all-in (~$13-14/month).** Exceeds the cap. I will not do this without your OK.

My pick: option 1, subject to verifying the Postgres provider's free terms. Be aware $10 total buys about one month of an always-on demo, not a permanent site.

## 6. Journeys, tools, evals

Order of build: A (damaged order), B (foundation), C+D (returning customer), E (gift), then minimal counter finder. Tools per spec section 5. Eval suite ~40 cases across the six categories, baseline first, results saved with dates in `eval/results/`. Thresholds from spec section 10 (100% guardrails, 90% others, 3 fix attempts, then log and move on).

## 7. Blocking issue: data

I cannot verify products or the returns policy yet. See `docs/source_access.md`. Journeys A and E depend on the verified policy text; B, C+D, E depend on verified products and fragrance notes. I can build the code, schema, fictional data, router, tool plumbing, UI, and eval harness without it, but nothing Armani-specific can be loaded or claimed until the data issue is resolved.

## 8. Build order (after approval)
1. Schema, seed fictional customers/orders, tool layer with identity enforcement.
2. Session model, Gemini swap, new router, trace output.
3. Journey A with evals; loop up to 3 fixes.
4. Verified data load as pages become available; journey B; then C+D; then E; then counter finder.
5. UI panel, disclaimers, scenario buttons.
6. Eval baseline and final runs, README, deploy, recorded fallback demo.
