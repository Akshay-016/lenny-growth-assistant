import pytest

from backend.app.database import AsyncSessionLocal
from backend.app.rag.retriever import TranscriptRetriever


@pytest.fixture
def retriever():
    return TranscriptRetriever()


@pytest.mark.asyncio
async def test_retriever_returns_relevant_results(retriever):
    query = "How should product teams decide what features to build?"

    async with AsyncSessionLocal() as session:
        results = await retriever.search(
            query=query,
            session=session,
        )

    assert isinstance(results, list)
    assert len(results) > 0

    for result in results:
        assert result.episode_title
        assert result.content
        assert result.source_path
        assert 0 <= result.similarity <= 1


@pytest.mark.asyncio
async def test_retriever_respects_top_k(retriever):
    query = "How do startups find product market fit?"

    async with AsyncSessionLocal() as session:
        results = await retriever.search(
            query=query,
            session=session,
            top_k=3,
        )

    assert len(results) <= 3


@pytest.mark.asyncio
async def test_retriever_empty_query(retriever):
    async with AsyncSessionLocal() as session:
        results = await retriever.search(
            query="",
            session=session,
        )

    assert results == []


@pytest.mark.asyncio
async def test_retriever_high_threshold_can_return_empty(retriever):
    query = "What is the recipe for making chocolate cake?"

    async with AsyncSessionLocal() as session:
        results = await retriever.search(
            query=query,
            session=session,
            similarity_threshold=0.99,
        )

    assert isinstance(results, list)
    assert len(results) == 0