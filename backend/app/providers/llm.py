from abc import ABC, abstractmethod

import httpx
from anthropic import AsyncAnthropic

from backend.app.config import get_settings


class LLMProvider(ABC):
    """
    Common interface for all LLM providers.

    The rest of the application should depend on this interface
    instead of directly depending on Ollama, Anthropic, etc.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 256,
    ) -> str:
        raise NotImplementedError


class OllamaLLMProvider(LLMProvider):
    """
    Local LLM provider using Ollama.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ):
        settings = get_settings()

        self.base_url = (
            base_url or settings.ollama_base_url
        ).rstrip("/")

        self.model = model or settings.ollama_model

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 256,
    ) -> str:
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        if max_tokens <= 0:
            raise ValueError(
                "max_tokens must be greater than zero."
            )

        messages = []

        if system_prompt and system_prompt.strip():
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt.strip(),
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt.strip(),
            }
        )

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        url = f"{self.base_url}/api/chat"

        timeout = httpx.Timeout(
            connect=10.0,
            read=300.0,
            write=30.0,
            pool=30.0,
        )

        async with httpx.AsyncClient(
            timeout=timeout
        ) as client:
            response = await client.post(
                url,
                json=payload,
            )

        response.raise_for_status()

        data = response.json()

        message = data.get("message")

        if not message:
            raise ValueError(
                "Ollama returned no message."
            )

        content = message.get("content")

        if not content:
            raise ValueError(
                "Ollama returned an empty response."
            )

        return content.strip()


class AnthropicLLMProvider(LLMProvider):
    """
    Cloud LLM provider using the official Anthropic Python SDK.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        settings = get_settings()

        self.api_key = (
            api_key or settings.anthropic_api_key
        ).strip()

        self.model = (
            model or settings.anthropic_model
        ).strip()

        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required when "
                "the Anthropic provider is selected."
            )

        if not self.model:
            raise ValueError(
                "ANTHROPIC_MODEL must be configured."
            )

        self.client = AsyncAnthropic(
            api_key=self.api_key,
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 256,
    ) -> str:
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        if max_tokens <= 0:
            raise ValueError(
                "max_tokens must be greater than zero."
            )

        request_kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt.strip(),
                }
            ],
        }

        if system_prompt and system_prompt.strip():
            request_kwargs["system"] = system_prompt.strip()

        # Current Claude models do not need a custom temperature.
        # We intentionally omit temperature from the API request.
        response = await self.client.messages.create(
            **request_kwargs,
        )

        text_parts: list[str] = []

        for block in response.content:
            if getattr(block, "type", None) == "text":
                text = getattr(block, "text", "")
                if text:
                    text_parts.append(text)

        content = "".join(text_parts).strip()

        if not content:
            raise ValueError(
                "Anthropic returned an empty response."
            )

        return content


def get_llm_provider(
    provider_name: str | None = None,
) -> LLMProvider:
    """
    Return the configured LLM provider.
    """

    settings = get_settings()

    provider = (
        provider_name
        or settings.default_llm_provider
    ).lower()

    if provider == "ollama":
        return OllamaLLMProvider()

    if provider == "anthropic":
        return AnthropicLLMProvider()

    raise ValueError(
        f"Unsupported LLM provider: {provider}"
    )