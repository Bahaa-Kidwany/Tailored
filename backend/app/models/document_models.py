"""
Re-export document models from app.models.document for backward compatibility.
"""
from app.models.document import GeneratedDocumentDB, utc_now

__all__ = ["GeneratedDocumentDB", "utc_now"]
