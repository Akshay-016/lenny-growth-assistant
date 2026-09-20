from pathlib import Path

import pytest

from backend.app.rag.ingestion import (
    TranscriptIngestionService,
)


TRANSCRIPTS_ROOT = Path(
    "data/raw/lennys-podcast-transcripts"
)


@pytest.mark.asyncio
async def test_prepare_document_generates_embeddings():
    service = TranscriptIngestionService(
        TRANSCRIPTS_ROOT
    )

    transcripts = service.loader.find_transcripts()

    assert transcripts

    records = await service.prepare_document(
        transcripts[0]
    )

    assert records

    first_record = records[0]

    assert first_record["episode_title"]
    assert first_record["content"]

    assert isinstance(
        first_record["embedding"],
        list,
    )

    assert len(
        first_record["embedding"]
    ) == 768

    assert all(
        isinstance(value, float)
        for value in first_record["embedding"]
    )