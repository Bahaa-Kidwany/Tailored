from collections import defaultdict
import threading
import time
from typing import Any, Callable, Dict, Optional
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from tailored_kit.audit.middleware import TraceAndFeatureMiddleware
from tailored_kit.config import ServiceSettings
from tailored_kit.errors import register_error_handlers
from tailored_kit.telemetry_otel.logging import configure_logging
from tailored_kit.telemetry_otel.setup import setup_telemetry


class _PrometheusMetrics:
    """Zero-dependency thread-safe Prometheus exposition registry per microservice."""

    def __init__(self, service_name: str) -> None:
        self.service_name = service_name
        self._lock = threading.Lock()
        self._counts: Dict[tuple[str, str, str], int] = defaultdict(int)
        self._dur_sum: Dict[tuple[str, str], float] = defaultdict(float)
        self._dur_cnt: Dict[tuple[str, str], int] = defaultdict(int)

    def observe(self, method: str, path: str, status: int, duration_s: float) -> None:
        with self._lock:
            self._counts[(method, path, str(status))] += 1
            self._dur_sum[(method, path)] += duration_s
            self._dur_cnt[(method, path)] += 1

    def render(self) -> str:
        lines = [
            "# HELP tailored_http_requests_total Total HTTP requests handled.",
            "# TYPE tailored_http_requests_total counter",
        ]
        with self._lock:
            for (method, path, status), cnt in sorted(self._counts.items()):
                lines.append(
                    f'tailored_http_requests_total{{service="{self.service_name}",method="{method}",path="{path}",status="{status}"}} {cnt}'
                )
            lines.extend(
                [
                    "# HELP tailored_http_request_duration_seconds Total HTTP latency and request count.",
                    "# TYPE tailored_http_request_duration_seconds summary",
                ]
            )
            for (method, path), total_s in sorted(self._dur_sum.items()):
                cnt = self._dur_cnt[(method, path)]
                lines.append(
                    f'tailored_http_request_duration_seconds_sum{{service="{self.service_name}",method="{method}",path="{path}"}} {total_s:.6f}'
                )
                lines.append(
                    f'tailored_http_request_duration_seconds_count{{service="{self.service_name}",method="{method}",path="{path}"}} {cnt}'
                )
        return "\n".join(lines) + "\n"


def create_service_app(
    settings: ServiceSettings,
    *,
    title: Optional[str] = None,
    lifespan: Optional[Callable[[FastAPI], Any]] = None,
    health_check_fn: Optional[Callable[[FastAPI], dict]] = None,
) -> FastAPI:
    """Factory creating a FastAPI microservice pre-wired with OTel, JSON logging, RFC 7807 errors, /metrics, and /health."""
    configure_logging(settings.service_name, settings.log_level)

    app = FastAPI(
        title=title or settings.service_name,
        version=settings.service_version,
        lifespan=lifespan,
    )
    app.state.settings = settings
    metrics_reg = _PrometheusMetrics(settings.service_name)
    app.state.prometheus_metrics = metrics_reg

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

    @app.middleware("http")
    async def prometheus_metrics_middleware(request: Request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)
        t0 = time.perf_counter()
        response = await call_next(request)
        route = request.scope.get("route")
        path_label = getattr(route, "path", request.url.path)
        metrics_reg.observe(request.method, path_label, response.status_code, time.perf_counter() - t0)
        return response

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

    @app.get("/metrics", tags=["health"])
    async def metrics():
        return PlainTextResponse(metrics_reg.render(), media_type="text/plain; version=0.0.4; charset=utf-8")

    return app
