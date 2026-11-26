from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceSettings(BaseSettings):
    """Base configuration shared across all Tailored microservices."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "tailored-service"
    service_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"

    database_url: str = ""
    redis_url: str = "redis://redis:6379/0"
    redpanda_brokers: str = "redpanda:9092"

    otlp_endpoint: str = "http://otel-collector:4317"
    otel_enabled: bool = True

    jwks_url: str = "http://auth-service:8001/.well-known/jwks.json"
    internal_hmac_secret: str = "dev_internal_hmac_secret_change_in_prod"
    audit_actor_salt: str = "dev_audit_actor_salt_change_in_prod"

    cors_allow_origins: list[str] = ["*"]
    default_feature_key: Optional[str] = None
