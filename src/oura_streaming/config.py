"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Oura OAuth2
    oura_client_id: str = ""
    oura_client_secret: str = ""
    oura_webhook_secret: str = ""
    oura_redirect_uri: str = "http://localhost:8000/auth/callback"

    # Oura API URLs
    oura_auth_url: str = "https://cloud.ouraring.com/oauth/authorize"
    oura_token_url: str = "https://api.ouraring.com/oauth/token"
    oura_api_base_url: str = "https://api.ouraring.com/v2"

    # Application
    app_secret_key: str = "change-me-in-production"
    debug: bool = False
    database_url: str = "sqlite+aiosqlite:///./oura_streaming.db"

    # Event store
    max_events: int = 1000
    # Storage backend: "sqlite" (default) or "warehouse" (Databricks SQL/Delta)
    storage_backend: str = "sqlite"

    # Databricks SQL (for storage_backend == "warehouse")
    # Example host: "adb-1234567890123.12.azuredatabricks.net"
    databricks_host: str = ""
    # HTTP path for SQL Warehouse, e.g., "/sql/1.0/warehouses/xxxxxxxxxxxx"
    databricks_http_path: str = ""
    # Personal Access Token or OAuth token with SQL access
    databricks_token: str = ""
    # Fully-qualified Delta table name to store events
    # Use hive_metastore.default by default to work without UC
    delta_table: str = "hive_metastore.default.oura_events"

    # Zerobus Ingest (streaming write sink — optional, uses SP OAuth M2M)
    # Note: distinct from databricks_token (PAT for DBSQL reads)
    databricks_workspace_url: str = ""       # e.g. https://dbc-xxx.cloud.databricks.com
    databricks_client_id: str = ""           # Service principal client ID
    databricks_client_secret: str = ""       # Service principal secret
    zerobus_server_endpoint: str = ""        # e.g. 12345.zerobus.us-east-1.cloud.databricks.com
    zerobus_table_name: str = ""             # e.g. main.default.oura_events

    @property
    def zerobus_enabled(self) -> bool:
        return all([
            self.databricks_workspace_url,
            self.databricks_client_id,
            self.databricks_client_secret,
            self.zerobus_server_endpoint,
            self.zerobus_table_name,
        ])

    # Polling (for Databricks Apps without public ingress)
    polling_enabled: bool = False
    polling_interval_seconds: int = 300
    poll_lookback_days: int = 1
    poll_data_types: str = "daily_sleep"
    # Optional bootstrap refresh token to obtain first access token without OAuth callback
    oura_initial_refresh_token: str = ""


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
