from types import SimpleNamespace

import pytest

from backend.app.rag.retriever import RetrievalResult
from backend.app.skills.ship30_generator import (
    Ship30Generator,
    Ship30Response,
)
from backend.app.skills.ship30 import Ship30For30Skill


class FakeRetriever:
    def __init__(self, results):
        self.results = results
        self.last_query = None

    async def search(
        self,
        query,
        session,
        top_k=None,
        similarity_threshold=None,
    ):
        self.last_query = query
        return self.results


class FakeLLMProvider:
    def __init__(self, response="Generated Ship 30 article"):
        self.response = response
        self.last_prompt = None
        self.last_system_prompt = None
        self.last_temperature = None
        self.last_max_tokens = None

    async def generate(
        self,
        prompt,
        system_prompt=None,
        temperature=0.2,
        max_tokens=256,
    ):
        self.last_prompt = prompt
        self.last_system_prompt = system_prompt
        self.last_temperature = temperature
        self.last_max_tokens = max_tokens

        return self.response


def make_retrieval_result(
    content="Product teams should start with customer problems.",
    episode_title="Test Product Episode",
    episode_url="https://example.com/test-episode",
    chunk_index=3,
    similarity=0.84,
    source_path="episodes/test/transcript.md",
):
    return RetrievalResult(
        id="test-id",
        episode_title=episode_title,
        episode_url=episode_url,
        content=content,
        chunk_index=chunk_index,
        similarity=similarity,
        source_path=source_path,
    )


def test_ship30_response_dataclass():
    response = Ship30Response(
        article="Test article",
        sources=[],
        retrieved_chunks=[],
        grounded=True,
    )

    assert response.article == "Test article"
    assert response.sources == []
    assert response.retrieved_chunks == []
    assert response.grounded is True


@pytest.mark.asyncio
async def test_empty_topic_does_not_retrieve_or_generate():
    retriever = FakeRetriever([])
    llm = FakeLLMProvider()

    generator = Ship30Generator(
        retriever=retriever,
        llm_provider=llm,
    )

    response = await generator.generate(
        topic="",
        session=SimpleNamespace(),
    )

    assert response.grounded is False
    assert response.sources == []
    assert response.retrieved_chunks == []
    assert "Please provide a topic" in response.article

    assert retriever.last_query is None
    assert llm.last_prompt is None


@pytest.mark.asyncio
async def test_no_retrieval_evidence_does_not_generate():
    retriever = FakeRetriever([])
    llm = FakeLLMProvider()

    generator = Ship30Generator(
        retriever=retriever,
        llm_provider=llm,
    )

    response = await generator.generate(
        topic="How should product teams prioritize features?",
        session=SimpleNamespace(),
    )

    assert response.grounded is False
    assert response.sources == []
    assert response.retrieved_chunks == []

    assert (
        "couldn't find enough relevant information"
        in response.article
    )

    assert retriever.last_query == (
        "How should product teams prioritize features?"
    )

    assert llm.last_prompt is None


@pytest.mark.asyncio
async def test_retrieved_evidence_is_passed_to_skill():
    chunk = make_retrieval_result()

    retriever = FakeRetriever([chunk])
    llm = FakeLLMProvider(
        response="# How to Prioritize Product Features\n\n"
        "Start with customer problems."
    )

    skill = Ship30For30Skill()

    generator = Ship30Generator(
        retriever=retriever,
        llm_provider=llm,
        skill=skill,
    )

    response = await generator.generate(
        topic="How should product teams prioritize features?",
        session=SimpleNamespace(),
    )

    assert response.grounded is True
    assert response.article.startswith("# How to Prioritize")

    assert llm.last_prompt is not None
    assert (
        "How should product teams prioritize features?"
        in llm.last_prompt
    )
    assert (
        "Product teams should start with customer problems."
        in llm.last_prompt
    )
    assert "Test Product Episode" in llm.last_prompt
    assert "episodes/test/transcript.md" not in llm.last_prompt


@pytest.mark.asyncio
async def test_llm_receives_ship30_system_prompt():
    chunk = make_retrieval_result()

    retriever = FakeRetriever([chunk])
    llm = FakeLLMProvider(
        response="# Test Article\n\nGrounded content."
    )

    generator = Ship30Generator(
        retriever=retriever,
        llm_provider=llm,
    )

    response = await generator.generate(
        topic="Product prioritization",
        session=SimpleNamespace(),
    )

    assert response.grounded is True
    assert llm.last_system_prompt is not None

    assert "Ship 30 for 30" in llm.last_system_prompt
    assert "PRACTICAL TAKEAWAY" in llm.last_system_prompt
    assert "Lenny transcript evidence" in llm.last_system_prompt


@pytest.mark.asyncio
async def test_conversation_context_is_passed_to_skill():
    chunk = make_retrieval_result()

    retriever = FakeRetriever([chunk])
    llm = FakeLLMProvider(
        response="# Product Prioritization\n\n"
        "Grounded article."
    )

    generator = Ship30Generator(
        retriever=retriever,
        llm_provider=llm,
    )

    await generator.generate(
        topic="How should we prioritize features?",
        session=SimpleNamespace(),
        additional_context=(
            "The user previously asked for a practical framework "
            "for a small product team."
        ),
    )

    assert llm.last_prompt is not None
    assert "CURRENT CONVERSATION CONTEXT" in llm.last_prompt
    assert "small product team" in llm.last_prompt


@pytest.mark.asyncio
async def test_sources_are_built_from_retrieved_chunks():
    chunks = [
        make_retrieval_result(
            content="Evidence one.",
            episode_title="Episode One",
            episode_url="https://example.com/one",
            chunk_index=1,
            similarity=0.91,
            source_path="episodes/one/transcript.md",
        ),
        make_retrieval_result(
            content="Evidence two.",
            episode_title="Episode Two",
            episode_url="https://example.com/two",
            chunk_index=7,
            similarity=0.79,
            source_path="episodes/two/transcript.md",
        ),
    ]

    retriever = FakeRetriever(chunks)
    llm = FakeLLMProvider(
        response="# Test Article\n\nGrounded article."
    )

    generator = Ship30Generator(
        retriever=retriever,
        llm_provider=llm,
    )

    response = await generator.generate(
        topic="Product growth",
        session=SimpleNamespace(),
    )

    assert len(response.sources) == 2

    assert response.sources[0].source_number == 1
    assert response.sources[0].episode_title == "Episode One"
    assert response.sources[0].episode_url == (
        "https://example.com/one"
    )
    assert response.sources[0].chunk_index == 1
    assert response.sources[0].similarity == 0.91
    assert response.sources[0].source_path == (
        "episodes/one/transcript.md"
    )

    assert response.sources[1].source_number == 2
    assert response.sources[1].episode_title == "Episode Two"


@pytest.mark.asyncio
async def test_llm_temperature_is_low_for_grounded_writing():
    chunk = make_retrieval_result()

    retriever = FakeRetriever([chunk])
    llm = FakeLLMProvider(
        response="# Test Article\n\nGrounded article."
    )

    generator = Ship30Generator(
        retriever=retriever,
        llm_provider=llm,
    )

    await generator.generate(
        topic="Product strategy",
        session=SimpleNamespace(),
    )

    assert llm.last_temperature == 0.2
    assert llm.last_max_tokens == 1800


@pytest.mark.asyncio
async def test_accidental_sources_section_is_removed():
    chunk = make_retrieval_result()

    retriever = FakeRetriever([chunk])
    llm = FakeLLMProvider(
        response=(
            "# Product Strategy\n\n"
            "Grounded article.\n\n"
            "Sources:\n"
            "- Fake source"
        )
    )

    generator = Ship30Generator(
        retriever=retriever,
        llm_provider=llm,
    )

    response = await generator.generate(
        topic="Product strategy",
        session=SimpleNamespace(),
    )

    assert "Grounded article." in response.article
    assert "Sources:" not in response.article
    assert "Fake source" not in response.article