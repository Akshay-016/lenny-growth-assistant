import pytest

from backend.app.providers.embedding import (
    OllamaEmbeddingProvider,
)


@pytest.mark.asyncio
async def test_ollama_embedding():
    provider = OllamaEmbeddingProvider()

    embedding = await provider.embed(
        "How can I improve product onboarding?"
    )

    assert isinstance(
        embedding,
        list,
    )

    assert len(embedding) == 768

    assert all(
        isinstance(value, float)
        for value in embedding
    )


@pytest.mark.asyncio
async def test_ollama_batch_embeddings():
    provider = OllamaEmbeddingProvider()

    texts = [
        "How can I improve product onboarding?",
        "How should a startup measure retention?",
        "What makes a good product manager?",
    ]

    embeddings = await provider.embed_many(
        texts
    )

    assert len(embeddings) == len(texts)

    for embedding in embeddings:
        assert isinstance(
            embedding,
            list,
        )

        assert len(embedding) == 768

        assert all(
            isinstance(value, float)
            for value in embedding
        )