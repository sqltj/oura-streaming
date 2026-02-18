# Oura Streaming

Oura Ring API v2 webhook receiver with OAuth2 integration, persistent storage, and real-time dashboard.

## Features

- **OAuth2 Integration**: Securely authenticate with Oura Ring.
- **Persistent Storage**: SQLite backend ensures events and tokens survive server restarts.
- **Real-time Dashboard**: Live UI with WebSocket streaming to watch events as they arrive.
- **Webhook Security**: HMAC-SHA256 signature verification for all incoming data.
- **Auto-Pruning**: Background task to keep your database clean (30-day retention).

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- [ngrok](https://ngrok.com) (free account) for local development
- An [Oura developer app](https://cloud.ouraring.com/oauth/applications)

To install prerequisites:
```bash
# uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# ngrok
brew install ngrok
```

## Quick Start

### 1. Install dependencies

```bash
uv sync
```

### 2. Create your Oura app

1. Go to [Oura Developer Portal](https://cloud.ouraring.com/oauth/applications).
2. Create a new application.
3. Set the redirect URI to your ngrok URL + `/auth/callback` (see step 4).
4. Note your **Client ID**, **Client Secret**, and **Webhook Secret**.

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
OURA_CLIENT_ID=your_client_id
OURA_CLIENT_SECRET=your_client_secret
OURA_WEBHOOK_SECRET=your_webhook_secret_from_portal
OURA_REDIRECT_URI=https://your-ngrok-url.ngrok-free.dev/auth/callback
APP_SECRET_KEY=generate-a-random-secret-key
DEBUG=true
```

### 4. Start ngrok

In a separate terminal:
```bash
ngrok http 8000
```

Copy the `https://...ngrok-free.dev` URL and update both:
- The **redirect URI** in the Oura developer portal to `https://YOUR-URL.ngrok-free.dev/auth/callback`.
- `OURA_REDIRECT_URI` in your `.env` file to match.

### 5. Start the server

```bash
uv run fastapi dev src/oura_streaming/main.py
```

### 6. View the Dashboard

Open your browser to:
`http://localhost:8000/dashboard`

### 7. Authenticate & Subscribe

1. Visit `http://localhost:8000/auth/login` to authorize.
2. Use the `/subscriptions` endpoint (or the interactive docs at `/docs`) to register for data types like `daily_sleep`, `sleep`, or `workout`.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/dashboard` | GET | Real-time events dashboard |
| `/auth/login` | GET | Start OAuth flow |
| `/auth/status` | GET | Check persistent authentication status |
| `/webhooks` | POST | Receive & verify signed webhook events |
| `/events` | GET | View stored events from SQLite |
| `/ws/events` | WS | WebSocket stream for live events |
| `/docs` | GET | Interactive Swagger API documentation |

## Running Tests

```bash
# Sync dev dependencies
uv sync --extra dev

# Run tests with in-memory DB
DATABASE_URL=sqlite+aiosqlite:///:memory: uv run pytest
```

## Databricks (Free/Trial) Setup

You can run this app as a Databricks App and persist events to a Delta table (no Lakebase required). Because Apps are not publicly reachable, enable polling instead of webhooks.

1) Create a SQL Warehouse and Delta table

Run in SQL Editor (use hive_metastore for non-UC):
```sql
CREATE SCHEMA IF NOT EXISTS hive_metastore.default;
CREATE TABLE IF NOT EXISTS hive_metastore.default.oura_events (
  id STRING,
  received_at TIMESTAMP,
  data_type STRING,
  event_type STRING,
  user_id STRING,
  payload STRING
) USING DELTA;
```

2) Configure App environment

Set the following env vars in your Databricks App:
- STORAGE_BACKEND=warehouse
- DATABRICKS_HOST=adb-XXXX.azuredatabricks.net
- DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/XXXXXXXXXXXX
- DATABRICKS_TOKEN=<PAT with SQL access>
- DELTA_TABLE=hive_metastore.default.oura_events
- POLLING_ENABLED=true
- POLLING_INTERVAL_SECONDS=300
- OURA_CLIENT_ID, OURA_CLIENT_SECRET
- OURA_INITIAL_REFRESH_TOKEN=<see step 3>

Start command:
```bash
uv run uvicorn oura_streaming.main:app --host 0.0.0.0 --port ${PORT:-3000} --proxy-headers
```

3) Bootstrap the Oura token (one-time)

Complete OAuth locally, then copy the refresh token to your App:
```bash
# local dev
uv sync && uv run fastapi dev src/oura_streaming/main.py
# finish OAuth at /auth/login ... /auth/callback

# extract refresh token from local SQLite
sqlite3 oura_streaming.db "select refresh_token from tokens limit 1;"
```
Set the value as `OURA_INITIAL_REFRESH_TOKEN` in the App. The app will refresh and persist an access token automatically.

Notes:
- Apps are not reachable from the public internet; webhooks will not arrive. Polling ingests `daily_sleep` by default.
- Use `/health` to verify status and `/dashboard` to view recent events.

## Project Structure

```
oura-streaming/
├── src/oura_streaming/
│   ├── main.py              # App entry & background tasks
│   ├── config.py            # Pydantic settings
│   ├── api/routes/          # Auth, Webhooks, Dashboard, Subscriptions
│   ├── models/              # Pydantic & SQLAlchemy models
│   ├── services/            # OuraClient & SqliteEventStore
│   ├── core/                # Database & Security logic
│   └── templates/           # Dashboard HTML
├── tests/                   # Async test suite
└── oura_streaming.db        # Persistent SQLite database (generated)
```

## License

MIT
