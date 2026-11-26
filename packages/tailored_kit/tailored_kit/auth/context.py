from typing import Optional
from pydantic import BaseModel


class RequestContext(BaseModel):
    """Verified user/service identity attached to each request."""

    user_id: Optional[str] = None
    session_id: Optional[str] = None
    analytics_anon_id: Optional[str] = None
    role: str = "anonymous"
    is_internal: bool = False
    trace_id: str = "0" * 32
    feature_key: Optional[str] = None

    @property
    def is_authenticated(self) -> bool:
        return bool(self.user_id)
