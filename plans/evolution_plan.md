# Evolution Plan: Oura Streaming

This plan outlines the steps to transition the Oura Streaming receiver from an in-memory prototype to a robust, persistent local service.

## Phase 1: Persistence Layer (SQLite)
Currently, all events and OAuth tokens are lost when the server restarts. We will implement a SQLite backend.

- [ ] **Infrastructure**: Add `sqlalchemy` and `aiosqlite` to `pyproject.toml`.
- [ ] **Database Setup**: Create `src/oura_streaming/core/database.py` for async SQLite connection management.
- [ ] **Models**: Define SQLAlchemy models for:
    - `StoredEvent`: To persist webhook payloads.
    - `OAuthToken`: To persist the current access and refresh tokens.
- [ ] **Event Service**: Implement `SqliteEventStore` to replace the in-memory `deque`.
- [ ] **Token Service**: Update `OuraClient` to load/save tokens from the database.

## Phase 2: Security & Verification
Ensure the incoming webhooks are actually from Oura.

- [ ] **Signature Verification**: Implement verification logic using the Oura Webhook Secret.
- [ ] **Config**: Add `OURA_WEBHOOK_SECRET` to `.env` and `Settings`.

## Phase 3: Real-time Dashboard
Improve the visibility of incoming data.

- [ ] **WebSocket Support**: Add a `/ws/events` endpoint to stream new events to clients.
- [ ] **Basic UI**: Create a simple HTML/HTMX dashboard at `/dashboard` to visualize health data trends and recent events.

## Phase 4: Feature Completeness
- [ ] **Data Types**: Ensure all 14+ data types are correctly modeled and handled.
- [ ] **Cleanup**: Add a background task to prune old events (e.g., older than 30 days).

## Verification
- [ ] Add unit tests for SQLite storage.
- [ ] Verify token persistence across server restarts.
