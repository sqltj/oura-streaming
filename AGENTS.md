# Repository Guidelines

## Project Structure & Module Organization
- `src/oura_streaming/` – FastAPI app code.
  - `api/routes/` (HTTP + WS endpoints), `core/` (db, security), `models/` (Pydantic + SQLAlchemy), `services/` (clients, stores), `templates/` (dashboard HTML), `main.py` (entrypoint).
- `tests/` – pytest suite (async). Shared fixtures in `conftest.py`.
- `.env.example` – copy to `.env` for local secrets.

## Build, Test, and Development Commands
```bash
# Install
uv sync                    # prod deps
uv sync --extra dev        # + dev/test deps

# Run (dev auto-reload)
uv run fastapi dev src/oura_streaming/main.py

# Run (prod-ish)
uv run uvicorn oura_streaming.main:app --host 0.0.0.0 --port 8000

# Tests (in-memory DB)
DATABASE_URL=sqlite+aiosqlite:///:memory: uv run pytest -q
```

## Coding Style & Naming Conventions
- Python 3.11+, 4-space indent, type hints required for public functions.
- Modules/files: `snake_case.py`; classes: `PascalCase`; functions/vars: `snake_case`.
- Prefer small, single-purpose functions; keep I/O at edges (services/api).
- No formatter is enforced; keep Black-compatible style. If using `ruff`/`black` locally, use defaults.

## Testing Guidelines
- Frameworks: `pytest`, `pytest-asyncio`, `httpx` `AsyncClient` with `ASGITransport`.
- Name tests `tests/test_*.py`; group with classes and `@pytest.mark.asyncio`.
- Fast paths: unit tests for `services/` and `core/`; endpoint tests via `client` fixture.
- Example: `DATABASE_URL=sqlite+aiosqlite:///:memory: uv run pytest -q`.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`.
- Commits: imperative, present tense; include scope when helpful (e.g., `feat(api): add /subscriptions`).
- PRs: clear description (what/why), linked issue, test plan (commands, endpoints), and screenshots for UI changes (`/dashboard`). Keep PRs small and focused.

## Security & Configuration Tips
- Never commit secrets. Create `.env` from `.env.example` and set: `OURA_CLIENT_ID`, `OURA_CLIENT_SECRET`, `OURA_WEBHOOK_SECRET`, `OURA_REDIRECT_URI`, `APP_SECRET_KEY`.
- Set `DEBUG=false` and a strong `APP_SECRET_KEY` in production; ensure `OURA_WEBHOOK_SECRET` is configured (HMAC verification).
- Local DB defaults to SQLite; override with `DATABASE_URL` when needed (tests use in-memory).
