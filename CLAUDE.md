# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important

When the user corrects you on anything, update this file with the correction to prevent future mistakes.

## Commands

```bash
# Install dependencies
uv sync

# Install with dev dependencies (pytest)
uv sync --extra dev

# Run development server (APX - both backend + Vite frontend, preferred)
apx dev start        # detached, proxy at http://localhost:9001
apx dev start -a     # attached (follows logs, Ctrl+C to stop)
apx dev stop         # stop detached server
apx dev logs         # view logs

# Run development server (manual, backend only)
uv run fastapi dev src/oura_streaming/main.py

# Run all tests
uv run pytest

# Run single test file
uv run pytest tests/test_webhooks.py

# Run specific test
uv run pytest tests/test_webhooks.py::TestWebhookReceive::test_receive_webhook_event -v
```

## Dev Server Gotchas

- `fastapi dev` uses auto-reload: any file change restarts the server and **clears all in-memory state** (OAuth tokens, stored events)
- When the user is authenticated and the dev server is running, **batch all code changes before having the user re-authenticate**. Do not make incremental edits that each trigger a reload.
- The Oura webhook subscription API requires `x-client-id` and `x-client-secret` headers in addition to the Bearer token.

## Architecture

FastAPI application receiving Oura Ring API v2 webhooks with OAuth2 authentication.

**Request Flow:**
1. `api/routes/` - FastAPI routers handle HTTP requests
2. `services/` - Business logic (OuraClient for OAuth, EventStore for storage)
3. `models/` - Pydantic validation for webhook payloads and OAuth tokens

**Key Components:**
- `config.py` - pydantic-settings loads from `.env` file
- `services/event_store.py` - In-memory bounded deque (no database)
- `services/oura_client.py` - OAuth2 token exchange with Oura API
- `core/security.py` - CSRF state token management for OAuth flow

**Oura Webhook Pattern:**
- GET `/webhooks?verification_token=X&challenge=UUID` - Oura verifies endpoint ownership. Must respond with `{"challenge": "<UUID>"}` echoing back the `challenge` param (not the verification_token).
- POST `/webhooks` - Receives events with `data_type` (14 types) and `event_type` (create/update/delete)
- Subscription API (`api.ouraring.com/v2/webhook/subscription`) requires `x-client-id` and `x-client-secret` headers plus Bearer token

## Lessons Learned

### Environment & Config
- **`.env` vs `.env.example`**: pydantic-settings loads from `.env` only. The `.env.example` is a template — never put real credentials there (it gets committed to git). Always copy to `.env` first.
- **Redirect URI must match exactly**: The redirect URI in the Oura developer portal must be character-for-character identical to what the app sends (including `/auth/callback` path, `https://` scheme, no trailing slash).

### Oura API Quirks
- **Auth and API are on different domains**: Authorization is `cloud.ouraring.com`, but token exchange and all API calls go to `api.ouraring.com`. Don't use `cloud.ouraring.com` for token exchange (returns 404).
- **Webhook verification sends two params**: Oura GETs `callback_url?verification_token=X&challenge=UUID`. You must echo back the `challenge` UUID (not the verification_token) as `{"challenge": "<UUID>"}`.
- **Subscription creation requires `verification_token` in body**: Not just `callback_url`, `data_type`, and `event_type`.
- **Subscription API needs extra headers**: `x-client-id` and `x-client-secret` headers required in addition to the Bearer token.
- **Oura returns 201 for subscription creation**: Not 200. Use `response.is_success` (checks 2xx) instead of `response.status_code == 200`.
- **Subscription list returns a JSON array**: Not a dict. Endpoint return types must accommodate this (use `JSONResponse` or `list`).
- **Subscriptions expire in ~90 days**: They need periodic renewal.

### Development Workflow
- **Batch code changes before re-auth**: Every file edit triggers FastAPI dev server reload, which clears in-memory OAuth tokens. Make all code changes at once, then re-authenticate once.
- **ngrok free tier**: URL changes on restart. Update both the Oura portal redirect URI and `.env` when ngrok restarts.
- **Debug Oura API responses**: When Oura returns errors, log the full response (status code + body) rather than raising immediately. Oura error messages are helpful but brief.
- **APX strips dev extras**: `apx dev start` runs `uv sync` during preflight (without `--extra dev`), removing pytest/httpx. Run `uv sync --extra dev` after `apx dev start` to restore test deps.
- **APX must be installed as a uv tool**: `uv tool install /path/to/apx.whl` installs APX globally (`~/.local/bin/apx`). Do NOT use `uv pip install` — it goes into the project venv and gets removed on next `uv sync`.
- **APX required files**: `metadata-path = "src/oura_streaming/_metadata.py"` must be in `[tool.apx.metadata]` in pyproject.toml, and `src/oura_streaming/_metadata.py` must exist with `app_name`, `app_slug`, `app_entrypoint`, `api_prefix`, `dist_dir` variables.

## Oura API Reference

- OAuth URLs: `cloud.ouraring.com/oauth/authorize` (auth), `api.ouraring.com/oauth/token` (token exchange)
- API Base: `api.ouraring.com/v2`
- Data Types: tag, enhanced_tag, workout, session, sleep, daily_sleep, daily_readiness, daily_activity, daily_spo2, sleep_time, rest_mode_period, ring_configuration, daily_stress, daily_cycle_phases


<claude-mem-context>
# Recent Activity

<!-- This section is auto-generated by claude-mem. Edit content outside the tags. -->

*No recent activity*
</claude-mem-context>
