from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    app_name: str = "Webconsig Modern API"
    app_env: str = "development"
    app_debug: bool = True
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5174,http://127.0.0.1:5174"

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/webconsig"
    redis_url: str = "redis://localhost:6379/0"
    sql_echo: bool = False
    auto_create_tables: bool = False
    db_pool_size: int = 20
    db_max_overflow: int = 40
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800

    use_rabbitmq: bool = False
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    rabbitmq_exchange: str = "webconsig.events"

    log_level: str = "DEBUG"
    request_log_body_limit: int = 2000
    enable_request_audit: bool = True
    request_audit_exclude_paths: str = "/api/v1/health"

    api_host: str = "0.0.0.0"
    api_port: int = 8001
    api_workers: int = 2

    auth_enabled: bool = True
    auth_allow_dev_header_fallback: bool = True
    authz_enabled: bool = True

    keycloak_base_url: str = "http://localhost:18080"
    keycloak_realm: str = "webconsig"
    keycloak_client_id: str = "webconsig-frontend"
    keycloak_verify_tls: bool = False
    keycloak_jwks_cache_seconds: int = 300

    model_config = SettingsConfigDict(
        env_file=str(ROOT_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def excluded_paths(self) -> set[str]:
        return {path.strip() for path in self.request_audit_exclude_paths.split(",") if path.strip()}


settings = Settings()
