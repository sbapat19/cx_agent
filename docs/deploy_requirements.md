# Deploy requirements

Nothing here is purchased or signed up for. These are what you would need to provide. Prices come from Render's own documentation and articles read on 2026-11-02; confirm on the pricing page before paying.

## Platform (proposed, needs your approval)
- **Render** for the FastAPI backend (web service) and the React frontend (static site), with git-push deploys.
- Free web service: spins down after 15 minutes idle, about 30-60 seconds to restart. Not acceptable for a live demo.
- Starter web service: $7/month, always on.
- Render Postgres: free instance expires after 30 days; smallest paid tier is roughly $6-7/month. Render + Starter + smallest Postgres is about $13-14/month, which is above your $10 cap.
- Proposed way to fit the cap: Starter web service ($7/month) plus a free Postgres from another provider (Neon or Supabase). I have not verified their current free terms; I will check before recommending a final choice.

## Accounts you create
1. GitHub account/repo for this project (private or public is your call). Render needs read access via its GitHub app install.
2. Render account (Hobby workspace is $0; a card is required to move the web service to Starter).
3. Postgres provider account (if not Render).
4. Google AI Studio API key for Gemini.
5. Optional: a free uptime monitor (only if you choose the keep-warm route).

## Card on file / money
- **Gemini needs billing enabled** for a live demo: the free tier showed a limit of 20 requests per model per day on the owner's key (one chat turn uses 3-8 calls). LLM cost on paid tier is unverified: rough guess is under $1 per 100 chat turns and a few dollars per full 55-scenario eval run; measure it from Google's usage page before deploying.
- Render Starter web service: $7/month, charged to the card you add.
- Gemini: free tier needs no card. Paid tier needs a billing-enabled Google Cloud project; LLM cost for demos is expected to be cents, but unverified.
- Total cap you set: $10. Stop and ask before anything that would exceed it.

## Environment variables
| Name | Where set | Purpose |
|---|---|---|
| `GOOGLE_API_KEY` | Render backend service (secret) and local `.env` | Gemini access |
| `DATABASE_URL` | Render backend service | Postgres connection string |
| `SECRET_KEY` | Render backend service | Signs demo session tokens |
| `ALLOWED_ORIGIN` | Render backend service | Exact frontend URL for CORS (replaces `*`) |
| `VITE_API_URL` | Render static site build env | Backend URL for the frontend |

Never commit keys. `.env` stays in `.gitignore`.

## Domain / CORS
- No custom domain needed; the default `*.onrender.com` URLs work. Backend CORS will be locked to the frontend's exact URL.

## Deploy and update steps (once credentials exist)
1. Push repo to GitHub.
2. In Render, create the web service (backend) and static site (frontend) from the repo; add the env vars above.
3. Run the DB migration/seed script once (I will provide one command).
4. Every later update: `git push` to `main` redeploys automatically.

## What I still need from you before deploying
- Approval of the platform and the $10 plan.
- The accounts and keys above.
- A decision on the data issue in `docs/source_access.md`.

## Public site setup (prepared, not deployed)
- One service built from the `Dockerfile` (UI + API together). Set these on the host, never in the repo:
  - `GOOGLE_API_KEY` (a NEW key, not the one shown in earlier screenshots)
  - `DATABASE_URL` (Postgres, optional: SQLite works but resets on redeploy)
  - `APP_ENV=production` (already set by the Dockerfile): turns off `/debug/*` and `/demo/reset`, turns on the limits below
  - Optional: `RATE_LIMIT_MESSAGES` (default 20 per IP per 10 min), `RATE_LIMIT_WINDOW_SECONDS`, `DAILY_MESSAGE_CAP` (default 1500 messages/day across all visitors), `MAX_MESSAGE_CHARS` (default 1000), `GEMINI_MODEL`
- Public page title defaults to "Beauty Assistant" (build arg `VITE_BRAND_TITLE`). The footer disclaimer always shows.
- Also set a spending cap or budget alert on the Google Cloud project.
