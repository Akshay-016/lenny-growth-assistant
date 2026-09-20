import pytest

from backend.app.database import AsyncSessionLocal
from backend.app.rag.generator import RAGAnswerGenerator


@pytest.mark.asyncio
async def test_real_rag_answer():
    generator = RAGAnswerGenerator()

    query = (
        "How should product teams decide what features "
        "to build?"
    )

    async with AsyncSessionLocal() as session:
        response = await generator.answer(
            query=query,
            session=session,
            top_k=5,
            similarity_threshold=0.65,
        )

    assert response.grounded is True
    assert response.answer

    assert len(response.retrieved_chunks) > 0
    assert len(response.citations) > 0

    # Every returned citation must correspond to an actual
    # retrieved transcript chunk.
    assert len(response.citations) == len(
        response.retrieved_chunks
    )

    for citation in response.citations:
        assert citation.citation_number >= 1
        assert citation.episode_title
        assert 0 <= citation.similarity <= 1

    # The backend owns source metadata. It should not depend
    # on an LLM-generated References section.
    assert "References:" not in response.answer
    assert "Sources:" not in response.answer

    print("\n" + "=" * 80)
    print("RAG ANSWER")
    print("=" * 80)
    print(response.answer)

    print("\n" + "=" * 80)
    print("STRUCTURED SOURCES")
    print("=" * 80)

    for citation in response.citations:
        print(
            f"[{citation.citation_number}] "
            f"{citation.episode_title} | "
            f"similarity={citation.similarity:.4f}"
        )