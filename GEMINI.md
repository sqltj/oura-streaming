# Project Overview

This project is a Python-based webhook receiver for the Oura Ring API v2, built using the FastAPI framework. Its primary purpose is to receive real-time health data from an Oura Ring, handle Oura's OAuth2 authentication process, and store the incoming data events in a temporary, in-memory cache.

The application is designed for local development and testing, using `ngrok` to expose the local server to the internet for Oura's webhooks. It supports all 14 of Oura's data types.

## Key Technologies

*   **Backend:** Python 3.11+, FastAPI
*   **Package Manager:** `uv`
*   **Configuration:** `pydantic-settings` (from `.env` file)
*   **HTTP Client:** `httpx`
*   **Testing:** `pytest`, `pytest-asyncio`

## Architecture

The project follows a standard FastAPI structure:

*   `src/oura_streaming/main.py`: The main application entry point.
*   `src/oura_streaming/api/`: Contains API route definitions, separating concerns for authentication, webhooks, and subscriptions.
*   `src/oura_streaming/models/`: Defines Pydantic models for data validation and serialization (e.g., `WebhookEvent`).
*   `src/oura_streaming/services/`: Implements the business logic.
    *   `event_store.py`: An in-memory store for webhook events using a `deque`.
    *   `oura_client.py`: A client for interacting with the Oura API.
*   `src/oura_streaming/core/`: Contains core components like security utilities.
*   `tests/`: Contains the test suite.

# Building and Running

## 1. Installation

Install dependencies using `uv`:

```bash
uv sync
```

## 2. Configuration

Create a `.env` file from the example and fill in your Oura application credentials and `ngrok` URL:

```bash
cp .env.example .env
```

**`.env` file:**

```env
OURA_CLIENT_ID=your_client_id
OURA_CLIENT_SECRET=your_client_secret
OURA_REDIRECT_URI=https://your-ngrok-url.ngrok-free.dev/auth/callback
APP_SECRET_KEY=generate-a-random-secret-key
DEBUG=true
```

## 3. Running the Application

Start the FastAPI server:

```bash
uv run fastapi dev src/oura_streaming/main.py
```

The API will be available at `http://localhost:8000`.

## 4. Running Tests

Install development dependencies and run the test suite:

```bash
# Install dev dependencies (if not already done)
uv sync --extra dev

# Run tests
uv run pytest
```

# Development Conventions

*   **Configuration:** All configuration is managed via environment variables and loaded through the `Settings` class in `src/oura_streaming/config.py`. Do not commit the `.env` file.
*   **Styling:** The project uses `ruff` for linting and formatting, as inferred from the presence of `ruff` in `pyproject.toml`.
*   **Typing:** The codebase uses Python's type hints.
*   **Asynchronous Code:** The application is built with `asyncio` and `FastAPI`, so new endpoints and services should be written as `async` functions where appropriate.
*   **Dependency Management:** Dependencies are managed in `pyproject.toml` and locked with `uv.lock`. Use `uv` to add or update packages.
*   **Modularity:** The project is structured by feature (e.g., `api`, `models`, `services`), and new functionality should follow this pattern.
*   **In-Memory Storage:** The current implementation uses an in-memory `deque` for event storage, which means data is lost on restart. This is suitable for development but would need to be replaced with a persistent database for production use.
