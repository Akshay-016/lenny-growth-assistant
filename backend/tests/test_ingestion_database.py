from pathlib import Path

import pytest
from sqlalchemy import select

from backend.app.database import AsyncSessionLocal
from backend.app.models import TranscriptChunk
from backend.app.rag.ingestion import (
    TranscriptIngestionService,
)


TRANSCRIPTS_ROOT = Path(
    "data/raw/lennys-podcast-transcripts"
)


@pytest.mark.asyncio
async def test_store_document_is_idempotent():
    service = TranscriptIngestionService(
        TRANSCRIPTS_ROOT
    )

    transcripts = service.loader.find_transcripts()

    assert transcripts

    async with AsyncSessionLocal() as session:
        first_insert_count = (
            await service.store_document(
                transcripts[0],
                session,
            )
        )

        second_insert_count = (
            await service.store_document(
                transcripts[0],
                session,
            )
        )

        assert first_insert_count >= 0
        assert second_insert_count == 0

        result = await session.execute(
            select(TranscriptChunk).where(
                TranscriptChunk.source_path
                == str(transcripts[0])
            )
        )

        stored_chunks = result.scalars().all()

        assert len(stored_chunks) > 0

        for chunk in stored_chunks:
            assert chunk.embedding is not None
            assert len(chunk.embedding) == 768