from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import TranscriptChunk
from backend.app.providers.embedding import (
    OllamaEmbeddingProvider,
)
from backend.app.rag.chunker import TranscriptChunker
from backend.app.rag.loader import TranscriptLoader


class TranscriptIngestionService:
    """Loads transcripts, chunks them, generates embeddings, and stores them."""

    def __init__(
        self,
        transcripts_root: str | Path,
    ):
        self.loader = TranscriptLoader(
            transcripts_root
        )

        self.chunker = TranscriptChunker(
            chunk_size=650,
            overlap=100,
        )

        self.embedding_provider = (
            OllamaEmbeddingProvider()
        )

    async def prepare_document(
        self,
        path: Path,
    ) -> list[dict]:
        """Load one transcript and prepare its chunks."""

        document = self.loader.load_file(path)

        chunks = self.chunker.chunk(
            document.content
        )

        embeddings = await self.embedding_provider.embed_many(
            [chunk.content for chunk in chunks]
        )

        records = []

        for chunk, embedding in zip(
            chunks,
            embeddings,
        ):
            records.append(
                {
                    "episode_title": document.title,
                    "episode_url": document.episode_url,
                    "source_path": str(path),
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "embedding": embedding,
                }
            )

        return records

    async def store_document(
        self,
        path: Path,
        session: AsyncSession,
    ) -> int:
        """
        Store only new chunks from one transcript.

        Existing chunks are checked before embeddings are generated.
        """

        document = self.loader.load_file(path)

        chunks = self.chunker.chunk(
            document.content
        )

        if not chunks:
            return 0

        source_path = str(path)

        existing_result = await session.execute(
            select(TranscriptChunk.chunk_index).where(
                TranscriptChunk.source_path
                == source_path
            )
        )

        existing_indexes = set(
            existing_result.scalars().all()
        )

        new_chunks = [
            chunk
            for chunk in chunks
            if chunk.chunk_index
            not in existing_indexes
        ]

        if not new_chunks:
            return 0

        embeddings = (
            await self.embedding_provider.embed_many(
                [
                    chunk.content
                    for chunk in new_chunks
                ]
            )
        )

        for chunk, embedding in zip(
            new_chunks,
            embeddings,
        ):
            transcript_chunk = TranscriptChunk(
                episode_title=document.title,
                episode_url=document.episode_url,
                source_path=source_path,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                embedding=embedding,
            )

            session.add(
                transcript_chunk
            )

        await session.commit()

        return len(new_chunks)