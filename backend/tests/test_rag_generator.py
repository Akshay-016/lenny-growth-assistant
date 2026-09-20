import pytest

from backend.app.rag.generator import (
    RAGAnswerGenerator,
)
from backend.app.rag.retriever import RetrievalResult


class FakeRetriever:
    def __init__(self, results):
        self.results = results
        self.called = False

    async def search(
        self,
        query,
        session,
        top_k=None,
        similarity_threshold=None,
    ):
        self.called = True
        return self.results


class FakeLLMProvider:
    def __init__(self, response="Test grounded answer [1]."):
        self.response = response
        self.called = False
        self.last_prompt = None
        self.last_system_prompt = None

    async def generate(
        self,
        prompt,
        system_prompt=None,
        temperature=0.2,
    ):
        self.called = True
        self.last_prompt = prompt
        self.last_system_prompt = system_prompt
        return self.response


def make_retrieval_result():
    return RetrievalResult(
        id="test-id",
        episode_title="Test Product Episode",
        episode_url="https://example.com/episode",
        content=(
            "Product teams should focus on understanding "
            "customer problems before deciding what to build."
        ),
        chunk_index=0,
        similarity=0.82,
        source_path="data/test/transcript.md",
    )


@pytest.mark.asyncio
async def test_generator_returns_grounded_answer():
    retriever = FakeRetriever(
        [make_retrieval_result()]
    )

    llm = FakeLLMProvider(
        "Product teams should understand customer "
        "problems first [1]."
    )

    generator = RAGAnswerGenerator(
        retriever=retriever,
        llm_provider=llm,
    )

    response = await generator.answer(
        query="How should product teams decide what to build?",
        session=None,
    )

    assert response.grounded is True
    assert response.answer
    assert len(response.retrieved_chunks) == 1
    assert len(response.citations) == 1

    assert response.citations[0].citation_number == 1
    assert (
        response.citations[0].episode_title
        == "Test Product Episode"
    )

    assert retriever.called is True
    assert llm.called is True


@pytest.mark.asyncio
async def test_generator_includes_transcript_context_in_prompt():
    retriever = FakeRetriever(
        [make_retrieval_result()]
    )

    llm = FakeLLMProvider()

    generator = RAGAnswerGenerator(
        retriever=retriever,
        llm_provider=llm,
    )

    await generator.answer(
        query="What should product teams focus on?",
        session=None,
    )

    assert llm.called is True
    assert llm.last_prompt is not None

    assert (
        "Test Product Episode"
        in llm.last_prompt
    )

    assert (
        "customer problems"
        in llm.last_prompt
    )

    assert "[1]" in llm.last_prompt


@pytest.mark.asyncio
async def test_generator_does_not_call_llm_without_context():
    retriever = FakeRetriever([])

    llm = FakeLLMProvider()

    generator = RAGAnswerGenerator(
        retriever=retriever,
        llm_provider=llm,
    )

    response = await generator.answer(
        query="What is the meaning of life?",
        session=None,
    )

    assert response.grounded is False
    assert response.citations == []
    assert response.retrieved_chunks == []
    assert llm.called is False
    assert "couldn't find enough relevant information" in (
        response.answer.lower()
    )


@pytest.mark.asyncio
async def test_generator_handles_empty_query():
    retriever = FakeRetriever([])

    llm = FakeLLMProvider()

    generator = RAGAnswerGenerator(
        retriever=retriever,
        llm_provider=llm,
    )

    response = await generator.answer(
        query="   ",
        session=None,
    )

    assert response.grounded is False
    assert response.citations == []
    assert response.retrieved_chunks == []
    assert retriever.called is False
    assert llm.called is False