import logging
from typing import Optional, List
from app.ai.providers.base import BaseLLMProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Google Vertex AI / Gemini LLM Provider supporting google-genai SDK."""

    def __init__(self):
        self.project = (settings.google_cloud_project or "").strip()
        self.location = (settings.google_cloud_location or "global").strip()
        self.model_name = (settings.gemini_model or "gemini-2.5-flash").strip()
        self._genai_client = None
        self._legacy_client = None

    def _get_genai_client(self):
        if self._genai_client is None:
            from google import genai
            self._genai_client = genai.Client(
                vertexai=True,
                project=self.project,
                location=self.location,
            )
        return self._genai_client

    def _get_legacy_vertex_client(self):
        if self._legacy_client is None:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            vertexai.init(project=self.project, location=self.location)
            self._legacy_client = GenerativeModel(self.model_name)
        return self._legacy_client

    def generate(
        self,
        system_prompt: str,
        user_text: str,
        images: Optional[List[str]] = None,
        temperature: float = 0.2,
    ) -> str:
        # 1. Try modern google-genai SDK first
        try:
            from google.genai import types
            client = self._get_genai_client()
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                thinking_config=types.ThinkingConfig(thinking_budget=512),
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            )
            response = client.models.generate_content(
                model=self.model_name,
                contents=user_text,
                config=config,
            )
            if response and response.text:
                return response.text
        except Exception as exc:
            logger.warning("google-genai Vertex AI call failed (%s); trying legacy vertexai.", exc)

        # 2. Try legacy vertexai SDK if installed
        try:
            client = self._get_legacy_vertex_client()
            prompt_parts = [system_prompt, "\n\n", user_text]
            response = client.generate_content(
                prompt_parts,
                generation_config={"temperature": temperature},
            )
            if response and response.text:
                return response.text
        except Exception as exc:
            logger.info("VertexAI unavailable (%s); falling back to MockLLMProvider.", exc)

        from app.ai.providers.mock_provider import MockLLMProvider
        return MockLLMProvider().generate(
            system_prompt=system_prompt,
            user_text=user_text,
            images=images,
            temperature=temperature,
        )
