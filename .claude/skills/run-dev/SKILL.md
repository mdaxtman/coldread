---
name: run-dev
description: Use when starting, restarting, or health-checking the ColdRead dev servers — "fire up the servers", "run the app", "is the backend up", or before any browser/E2E verification of the app.
---

# Run ColdRead Dev Servers

Two independent processes, no shared server: FastAPI backend on `:8000`, Vite frontend on `:5173`. The client calls the backend cross-origin via `VITE_API_URL ?? 'http://localhost:8000'` (`client/src/api/client.ts`) — there is **no Vite proxy**.

## Pre-flight: check for zombies first

A port that's listening is NOT proof of a healthy server — orphaned uvicorn processes from killed terminals have squatted on `:8000` before (often started without `--reload`, so they silently ignore code changes).

```bash
lsof -iTCP -sTCP:LISTEN -P -n | grep -E ':(8000|5173)'
```

If something is on `:8000`, verify it responds AND has `--reload` in its command line (`ps -o command -p <pid>`). If either check fails, kill it and start fresh:

```bash
kill <pid>   # or: pkill -f 'uvicorn main:app'
```

## Launch (both in background)

```bash
# Backend — MUST include --reload (equivalent of `make dev` in server/)
cd server && uv run uvicorn main:app --reload --port 8000

# Frontend
cd client && npm run dev
```

Backend needs `server/.env` (ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY, DEFAULT_USER_ID, ADMIN_PASSWORD) — it exists locally and is gitignored; never edit it.

## Verify (launching ≠ running)

```bash
curl -s http://127.0.0.1:8000/health   # → {"status":"ok"}
curl -s http://localhost:5173/ -o /dev/null -w "%{http_code}"   # → 200 (URL first — matches the permission allowlist prefix)
```

`GET /` on the backend returns 404 — that's normal (no root route). Use `/health`, or `/docs` for the OpenAPI UI.

## Gotchas

| Symptom | Cause |
|---|---|
| UI loads but API calls fail in browser console only | CORS — two-origin setup; `curl` succeeding proves nothing about browser fetches |
| Python edits not taking effect | uvicorn running without `--reload` (likely a zombie) |
| Backend 500s mentioning RLS / 42501 | Supabase project paused or wrong key type — see supabase-environment-gotchas memory |
