from pathlib import Path

from backend.app.rag.chunker import TranscriptChunker
from backend.app.rag.loader import TranscriptLoader


TRANSCRIPTS_ROOT = Path(
    "data/raw/lennys-podcast-transcripts"
)


def test_loader_to_chunker_pipeline():
    loader = TranscriptLoader(
        TRANSCRIPTS_ROOT
    )

    transcripts = loader.find_transcripts()

    assert transcripts

    document = loader.load_file(
        transcripts[0]
    )

    chunker = TranscriptChunker(
        chunk_size=650,
        overlap=100,
    )

    chunks = chunker.chunk(
        document.content
    )

    assert chunks

    assert all(
        chunk.content
        for chunk in chunks
    )

    assert chunks[0].chunk_index == 0


def test_chunk_metadata_matches_transcript():
    loader = TranscriptLoader(
        TRANSCRIPTS_ROOT
    )

    transcript = loader.load_file(
        loader.find_transcripts()[0]
    )

    chunker = TranscriptChunker(
        chunk_size=650,
        overlap=100,
    )

    chunks = chunker.chunk(
        transcript.content
    )

    for index, chunk in enumerate(chunks):
        assert chunk.chunk_index == index
        assert isinstance(
            chunk.content,
            str,
        )
        assert len(
            chunk.content.split()
        ) > 0