from typing import Any, Callable, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tailored_kit.audit.middleware import TraceAndFeatureMiddleware
from tailored_kit.config import ServiceSettings
from tailored_kit.errors import register_error_handlers
from tailored_kit.telemetry_otel.logging import configure_logging
from tailored_kit.telemetry_otel.setup import setup_telemetry


def create_service_app(
    settings: ServiceSettings,
    *,
    title: Optional[str] = None,
    lifespan: Optional[Callable[[FastAPI], Any]] = None,
    health_check_fn: Optional[Callable[[FastAPI], dict]] = None,
) -> FastAPI:
    """Factory creating a FastAPI microservice pre-wired with OTel, JSON logging, RFC 7807 errors, and /health."""
    configure_logging(settings.service_name, settings.log_level)

    app = FastAPI(
        title=title or settings.service_name,
        version=settings.service_version,
        lifespan=lifespan,
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        TraceAndFeatureMiddleware,
        default_feature_key=settings.default_feature_key,
    )

    register_error_handlers(app)
    setup_telemetry(app, settings)

    @app.get("/health", tags=["health"])
    async def health():
        details = health_check_fn(app) if health_check_fn else {}
        return {
            "status": "ok",
            "service": settings.service_name,
            "version": settings.service_version,
            **details,
        }

    return app
