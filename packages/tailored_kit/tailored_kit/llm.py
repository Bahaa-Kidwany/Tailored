from __future__ import annotations

import logging
import math
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class LlmClient:
    """Async multi-provider LLM & embedding client (Gemini / OpenAI) with graceful fallback."""

    def __init__(
        self,
        *,
        gemini_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        gemini_model: Optional[str] = None,
        openai_model: Optional[str] = None,
        gemini_embed_model: Optional[str] = None,
        openai_embed_model: Optional[str] = None,
    ) -> None:
        self.gemini_api_key = (
            gemini_api_key if gemini_api_key is not None else os.getenv("GEMINI_API_KEY", "")
        ).strip()
        self.openai_api_key = (
            openai_api_key if openai_api_key is not None else os.getenv("OPENAI_API_KEY", "")
        ).strip()
        self.gemini_model = (gemini_model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")).strip()
        self.openai_model = (openai_model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")).strip()
        self.gemini_embed_model = (
            gemini_embed_model or os.getenv("GEMINI_EMBED_MODEL", "text-embedding-004")
        ).strip()
        self.openai_embed_model = (
            openai_embed_model or os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
        ).strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.gemini_api_key or self.openai_api_key)

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1200,
    ) -> Optional[str]:
        if not self.is_configured:
            return None

        if self.gemini_api_key:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{self.gemini_model}:generateContent"
            )
            payload = {
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                },
            }
            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.post(
                        url,
                        params={"key": self.gemini_api_key},
                        json=payload,
                    )
                    if resp.status_code < 400:
                        data = resp.json()
                        candidates = data.get("candidates") or []
                        if candidates:
                            parts = (candidates[0].get("content") or {}).get("parts") or []
                            text = "".join(str(p.get("text") or "") for p in parts).strip()
                            if text:
                                return text
                    else:
                        logger.warning("Gemini generateContent returned %s", resp.status_code)
            except Exception as exc:
                logger.warning("Gemini generateContent error: %s", exc)

        if self.openai_api_key:
            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {self.openai_api_key}"},
                        json={
                            "model": self.openai_model,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt},
                            ],
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                        },
                    )
                    if resp.status_code < 400:
                        data = resp.json()
                        choices = data.get("choices") or []
                        if choices:
                            content = ((choices[0].get("message") or {}).get("content") or "").strip()
                            if content:
                                return content
                    else:
                        logger.warning("OpenAI chat completions returned %s", resp.status_code)
            except Exception as exc:
                logger.warning("OpenAI chat completions error: %s", exc)

        return None

    async def embed_text(self, text: str, dim: int = 768) -> Optional[List[float]]:
        if not self.is_configured or not (text or "").strip():
            return None

        raw_vec: Optional[List[float]] = None

        if self.gemini_api_key:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{self.gemini_embed_model}:embedContent"
            )
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(
                        url,
                        params={"key": self.gemini_api_key},
                        json={
                            "content": {"parts": [{"text": text[:6000]}]},
                            "outputDimensionality": dim,
                        },
                    )
                    if resp.status_code < 400:
                        emb = (resp.json().get("embedding") or {}).get("values")
                        if isinstance(emb, list) and emb:
                            raw_vec = [float(x) for x in emb]
                    else:
                        logger.warning("Gemini embedContent returned %s", resp.status_code)
            except Exception as exc:
                logger.warning("Gemini embedContent error: %s", exc)

        if raw_vec is None and self.openai_api_key:
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/embeddings",
                        headers={"Authorization": f"Bearer {self.openai_api_key}"},
                        json={
                            "model": self.openai_embed_model,
                            "input": text[:6000],
                            "dimensions": dim,
                        },
                    )
                    if resp.status_code < 400:
                        rows = resp.json().get("data") or []
                        if rows and isinstance(rows[0].get("embedding"), list):
                            raw_vec = [float(x) for x in rows[0]["embedding"]]
                    else:
                        logger.warning("OpenAI embeddings returned %s", resp.status_code)
            except Exception as exc:
                logger.warning("OpenAI embeddings error: %s", exc)

        if not raw_vec:
            return None

        if len(raw_vec) < dim:
            raw_vec = raw_vec + [0.0] * (dim - len(raw_vec))
        elif len(raw_vec) > dim:
            raw_vec = raw_vec[:dim]

        norm = math.sqrt(sum(v * v for v in raw_vec)) or 1.0
        return [v / norm for v in raw_vec]


class LangfuseClient:
    """Lightweight async Langfuse ingestion client with no-op fallback when unconfigured."""

    def __init__(
        self,
        *,
        host: Optional[str] = None,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
    ) -> None:
        self.host = (host if host is not None else os.getenv("LANGFUSE_HOST", "")).strip().rstrip("/")
        self.public_key = (
            public_key if public_key is not None else os.getenv("LANGFUSE_PUBLIC_KEY", "")
        ).strip()
        self.secret_key = (
            secret_key if secret_key is not None else os.getenv("LANGFUSE_SECRET_KEY", "")
        ).strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.host and self.public_key and self.secret_key)

    async def _ingest(self, batch: List[Dict[str, Any]]) -> None:
        if not self.is_configured:
            return
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    f"{self.host}/api/public/ingestion",
                    auth=(self.public_key, self.secret_key),
                    json={"batch": batch},
                )
                if resp.status_code >= 400:
                    logger.warning("Langfuse ingestion returned %s", resp.status_code)
        except Exception as exc:
            logger.warning("Langfuse ingestion error: %s", exc)

    async def record_trace(
        self,
        trace_id: str,
        name: str,
        user_id: Optional[str],
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not self.is_configured:
            return
        await self._ingest(
            [
                {
                    "id": f"trace_{trace_id}",
                    "type": "trace-create",
                    "body": {
                        "id": trace_id,
                        "name": name,
                        "userId": user_id,
                        "input": input_data,
                        "output": output_data,
                        "metadata": metadata or {},
                    },
                }
            ]
        )

    async def record_score(
        self,
        trace_id: str,
        name: str,
        value: float,
        comment: Optional[str] = None,
    ) -> None:
        if not self.is_configured:
            return
        await self._ingest(
            [
                {
                    "id": f"score_{trace_id}_{name}",
                    "type": "score-create",
                    "body": {
                        "traceId": trace_id,
                        "name": name,
                        "value": value,
                        "comment": comment,
                    },
                }
            ]
        )
