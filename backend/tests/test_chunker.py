from backend.app.rag.chunker import TranscriptChunker


def test_chunker_creates_chunks():
    text = " ".join(
        f"word{i}"
        for i in range(1500)
    )

    chunker = TranscriptChunker(
        chunk_size=650,
        overlap=100,
    )

    chunks = chunker.chunk(text)

    assert len(chunks) > 1
    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1


def test_chunker_has_overlap():
    text = " ".join(
        f"word{i}"
        for i in range(800)
    )

    chunker = TranscriptChunker(
        chunk_size=650,
        overlap=100,
    )

    chunks = chunker.chunk(text)

    assert len(chunks) >= 2

    first_words = chunks[0].content.split()
    second_words = chunks[1].content.split()

    assert first_words[-100:] == second_words[:100]


def test_empty_text_returns_no_chunks():
    chunker = TranscriptChunker()

    assert chunker.chunk("") == []


def test_whitespace_only_returns_no_chunks():
    chunker = TranscriptChunker()

    assert chunker.chunk("   \n\t   ") == []