from pathlib import Path

from backend.app.rag.loader import TranscriptLoader


TRANSCRIPTS_ROOT = Path(
    "data/raw/lennys-podcast-transcripts"
)


def test_transcript_repository_exists():
    assert TRANSCRIPTS_ROOT.exists()


def test_transcripts_are_found():
    loader = TranscriptLoader(
        TRANSCRIPTS_ROOT
    )

    transcripts = loader.find_transcripts()

    assert len(transcripts) > 0
    assert all(
        path.name == "transcript.md"
        for path in transcripts
    )


def test_single_transcript_loads():
    loader = TranscriptLoader(
        TRANSCRIPTS_ROOT
    )

    transcripts = loader.find_transcripts()

    document = loader.load_file(
        transcripts[0]
    )

    assert document.title
    assert document.content
    assert document.source_path