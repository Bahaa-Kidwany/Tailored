from typing import Any, Dict, Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from tailored_kit.feature_context import get_current_feature_key
from tailored_kit.telemetry_otel.setup import get_current_trace_context


class ProblemDetail(BaseModel):
    """RFC 7807 error payload extended with Tailored trace and feature context."""

    type: str
    title: str
    status: int
    detail: str
    error_code: str
    trace_id: str
    feature_key: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TailoredError(Exception):
    """Base domain exception mapped automatically to RFC 7807 JSON."""

    status_code: int = 400
    error_code: str = "BAD_REQUEST"
    title: str = "Request Error"
    error_type: str = "https://tailored.app/errors/bad-request"

    def __init__(
        self,
        detail: str,
        *,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code
        if title is not None:
            self.title = title
        self.metadata = metadata or {}


class UnauthorizedError(TailoredError):
    status_code = 401
    error_code = "UNAUTHORIZED"
    title = "Authentication Required"
    error_type = "https://tailored.app/errors/unauthorized"


class InsufficientCreditsError(TailoredError):
    status_code = 402
    error_code = "INSUFFICIENT_CREDITS"
    title = "Insufficient Credits"
    error_type = "https://tailored.app/errors/insufficient-credits"


class ForbiddenError(TailoredError):
    status_code = 403
    error_code = "FORBIDDEN"
    title = "Access Forbidden"
    error_type = "https://tailored.app/errors/forbidden"


class NotFoundError(TailoredError):
    status_code = 404
    error_code = "NOT_FOUND"
    title = "Resource Not Found"
    error_type = "https://tailored.app/errors/not-found"


class ConflictError(TailoredError):
    status_code = 409
    error_code = "CONFLICT"
    title = "State Conflict"
    error_type = "https://tailored.app/errors/conflict"


def register_error_handlers(app: FastAPI) -> None:
    """Registers RFC 7807 exception handlers including trace_id and feature_key."""

    @app.exception_handler(TailoredError)
    async def handle_tailored_error(request: Request, exc: TailoredError) -> JSONResponse:
        trace_id, _ = get_current_trace_context()
        feature_key = (
            get_current_feature_key()
            or getattr(request.state, "feature_key", None)
            or request.headers.get("X-Feature-Key")
        )
        problem = ProblemDetail(
            type=exc.error_type,
            title=exc.title,
            status=exc.status_code,
            detail=exc.detail,
            error_code=exc.error_code,
            trace_id=trace_id,
            feature_key=feature_key,
            metadata=exc.metadata,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=problem.model_dump(),
            headers={"X-Trace-Id": trace_id},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        trace_id, _ = get_current_trace_context()
        feature_key = (
            get_current_feature_key()
            or getattr(request.state, "feature_key", None)
            or request.headers.get("X-Feature-Key")
        )
        problem = ProblemDetail(
            type="https://tailored.app/errors/internal-server-error",
            title="Internal Server Error",
            status=500,
            detail="An unexpected error occurred. Reference X-Trace-Id for diagnostics.",
            error_code="INTERNAL_SERVER_ERROR",
            trace_id=trace_id,
            feature_key=feature_key,
        )
        return JSONResponse(
            status_code=500,
            content=problem.model_dump(),
            headers={"X-Trace-Id": trace_id},
        )
