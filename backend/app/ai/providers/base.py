from abc import ABC, abstractmethod
from typing import Optional, List

class BaseLLMProvider(ABC):
    """Abstract interface for LLM backends (Vertex AI, Gemini, Ollama, OpenAI)."""

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_text: str,
        images: Optional[List[str]] = None,
        temperature: float = 0.2,
    ) -> str:
        """Generates raw text from the model given system prompt and user text."""
        pass
