import pytest

from backend.app.providers.llm import (
    LLMProvider,
    OllamaLLMProvider,
    get_llm_provider,
)


def test_ollama_provider_implements_llm_provider():
    provider = OllamaLLMProvider()

    assert isinstance(provider, LLMProvider)


def test_get_llm_provider_returns_ollama():
    provider = get_llm_provider("ollama")

    assert isinstance(provider, OllamaLLMProvider)


def test_unsupported_provider_raises_error():
    with pytest.raises(ValueError):
        get_llm_provider("unsupported")


@pytest.mark.asyncio
async def test_ollama_generate():
    provider = OllamaLLMProvider()

    response = await provider.generate(
        prompt="In one short sentence, what is product-market fit?"
    )

    assert isinstance(response, str)
    assert response.strip()


@pytest.mark.asyncio
async def test_ollama_generate_with_system_prompt():
    provider = OllamaLLMProvider()

    response = await provider.generate(
        system_prompt=(
            "You are a concise product management assistant."
        ),
        prompt=(
            "Explain product-market fit in one sentence."
        ),
        temperature=0.2,
    )

    assert isinstance(response, str)
    assert response.strip()


@pytest.mark.asyncio
async def test_ollama_empty_prompt_raises_error():
    provider = OllamaLLMProvider()

    with pytest.raises(ValueError):
        await provider.generate("")