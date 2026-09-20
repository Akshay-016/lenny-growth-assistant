from abc import ABC, abstractmethod

import httpx

from backend.app.config import get_settings


class EmbeddingProvider(ABC):
    """Interface for text embedding providers."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate an embedding for a single text."""
        raise NotImplementedError

    async def embed_many(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts."""

        embeddings = []

        for text in texts:
            embeddings.append(
                await self.embed(text)
            )

        return embeddings


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Embedding provider backed by Ollama."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str = "nomic-embed-text",
    ):
        settings = get_settings()

        self.base_url = (
            base_url or settings.ollama_base_url
        ).rstrip("/")

        self.model = model

    async def embed(
        self,
        text: str,
    ) -> list[float]:
        """Generate one embedding."""

        url = f"{self.base_url}/api/embed"

        payload = {
            "model": self.model,
            "input": text,
        }

        async with httpx.AsyncClient(
            timeout=60.0
        ) as client:
            response = await client.post(
                url,
                json=payload,
            )

        response.raise_for_status()

        data = response.json()

        embeddings = data.get("embeddings")

        if not embeddings:
            raise ValueError(
                "Ollama returned no embeddings."
            )

        embedding = embeddings[0]

        if len(embedding) != 768:
            raise ValueError(
                "Expected a 768-dimensional embedding, "
                f"but Ollama returned {len(embedding)} dimensions."
            )

        return embedding

    async def embed_many(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts in one Ollama request."""

        if not texts:
            return []

        url = f"{self.base_url}/api/embed"

        payload = {
            "model": self.model,
            "input": texts,
        }

        async with httpx.AsyncClient(
            timeout=120.0
        ) as client:
            response = await client.post(
                url,
                json=payload,
            )

        response.raise_for_status()

        data = response.json()

        embeddings = data.get("embeddings")

        if not embeddings:
            raise ValueError(
                "Ollama returned no embeddings."
            )

        if len(embeddings) != len(texts):
            raise ValueError(
                "Ollama returned an unexpected number "
                "of embeddings. "
                f"Expected {len(texts)}, "
                f"received {len(embeddings)}."
            )

        for embedding in embeddings:
            if len(embedding) != 768:
                raise ValueError(
                    "Expected a 768-dimensional embedding, "
                    f"but Ollama returned {len(embedding)} dimensions."
                )

        return embeddings