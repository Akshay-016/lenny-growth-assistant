from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.models import TranscriptChunk
from backend.app.providers.embedding import OllamaEmbeddingProvider


@dataclass
class RetrievalResult:
    id: str
    episode_title: str
    episode_url: str | None
    content: str
    chunk_index: int
    similarity: float
    source_path: str


class TranscriptRetriever:
    def __init__(
        self,
        embedding_provider: OllamaEmbeddingProvider | None = None,
    ):
        settings = get_settings()

        self.embedding_provider = (
            embedding_provider or OllamaEmbeddingProvider()
        )

        self.top_k = settings.retrieval_top_k
        self.similarity_threshold = (
            settings.retrieval_similarity_threshold
        )

    async def search(
        self,
        query: str,
        session: AsyncSession,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
    ) -> list[RetrievalResult]:

        query = query.strip()

        if not query:
            return []

        effective_top_k = top_k or self.top_k

        effective_threshold = (
            self.similarity_threshold
            if similarity_threshold is None
            else similarity_threshold
        )

        query_embedding = await self.embedding_provider.embed(query)

        distance = TranscriptChunk.embedding.cosine_distance(
            query_embedding
        )

        similarity = 1 - distance

        statement = (
            select(
                TranscriptChunk,
                similarity.label("similarity"),
            )
            .where(similarity >= effective_threshold)
            .order_by(distance)
            .limit(effective_top_k)
        )

        result = await session.execute(statement)

        rows = result.all()

        return [
            RetrievalResult(
                id=str(chunk.id),
                episode_title=chunk.episode_title,
                episode_url=chunk.episode_url,
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                similarity=float(score),
                source_path=chunk.source_path,
            )
            for chunk, score in rows
        ]