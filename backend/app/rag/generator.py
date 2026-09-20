from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.providers.llm import LLMProvider, get_llm_provider
from backend.app.rag.retriever import (
    RetrievalResult,
    TranscriptRetriever,
)


@dataclass
class SourceCitation:
    """A source used to ground the generated answer."""

    citation_number: int
    episode_title: str
    episode_url: str | None
    chunk_index: int
    similarity: float


@dataclass
class RAGResponse:
    """Final response returned by the RAG generation layer."""

    answer: str
    citations: list[SourceCitation]
    retrieved_chunks: list[RetrievalResult]
    grounded: bool


class RAGAnswerGenerator:
    """
    Generates answers grounded in Lenny's Podcast transcripts.

    The LLM generates only the answer.
    The backend owns the authoritative source metadata.
    """

    def __init__(
        self,
        retriever: TranscriptRetriever | None = None,
        llm_provider: LLMProvider | None = None,
    ):
        self.retriever = retriever or TranscriptRetriever()
        self.llm_provider = llm_provider or get_llm_provider()

    async def answer(
        self,
        query: str,
        session: AsyncSession,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
        conversation_context: str | None = None,
    ) -> RAGResponse:
        """Generate a grounded answer for a user query."""

        query = query.strip()

        if not query:
            return RAGResponse(
                answer=(
                    "Please provide a question about product, growth, "
                    "startups, or related topics discussed in "
                    "Lenny's Podcast."
                ),
                citations=[],
                retrieved_chunks=[],
                grounded=False,
            )

        retrieved_chunks = await self.retriever.search(
            query=query,
            session=session,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )

        if not retrieved_chunks:
            return RAGResponse(
                answer=(
                    "I couldn't find enough relevant information "
                    "in Lenny's Podcast transcripts to answer "
                    "that question reliably."
                ),
                citations=[],
                retrieved_chunks=[],
                grounded=False,
            )

        context = self._build_context(retrieved_chunks)

        system_prompt = """
You are Lenny Growth Assistant.

Answer the user's question using ONLY the supplied Lenny's
Podcast transcript excerpts.

Rules:

1. Answer the exact question asked.
2. Use only information supported by the supplied excerpts.
3. Do not use outside knowledge.
4. Do not invent facts, names, quotes, examples, or sources.
5. Do not create a References section.
6. Do not create a Sources section.
7. Do not create or modify citation numbers.
8. Do not mention an episode or guest unless supported by the
   supplied excerpts.
9. If the excerpts do not contain enough information, say so.
10. Be concise and directly useful.
11. Do not discuss the retrieval process.
12. Use the conversation context only to understand references,
    follow-up questions, and the user's intent.
13. The transcript excerpts remain the only source of factual
    knowledge.

The application handles source citations separately.
Do not generate citation numbers in your answer.
""".strip()

        conversation_section = ""

        if conversation_context and conversation_context.strip():
            conversation_section = f"""
CURRENT CONVERSATION CONTEXT
============================

{conversation_context.strip()}

Use this conversation context only to understand references,
follow-up questions, and the user's intent. Transcript excerpts
remain the only source of factual knowledge.
""".strip()

        prompt = f"""
Answer this question:

{query}

{conversation_section}

Use the following Lenny's Podcast transcript excerpts as your
only source of factual information:

{context}

Give a direct and concise answer.

Do not create a References or Sources section.
Do not discuss the retrieval process.
Do not create citation numbers.
""".strip()

        answer = await self.llm_provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.0,
        )

        answer = self._clean_answer(answer)

        citations = self._build_citations(
            retrieved_chunks
        )

        return RAGResponse(
            answer=answer,
            citations=citations,
            retrieved_chunks=retrieved_chunks,
            grounded=True,
        )

    @staticmethod
    def _build_context(
        chunks: list[RetrievalResult],
    ) -> str:
        """
        Build a compact numbered transcript context.

        The numbered format is intentionally retained because
        the generator tests expect numbered source context.

        Each chunk is limited to 1,500 characters so the local
        3B model receives a manageable prompt.
        """

        sections = []

        for index, chunk in enumerate(chunks, start=1):
            content = chunk.content[:1500]

            sections.append(
                "\n".join(
                    [
                        f"[{index}]",
                        f"Episode title: {chunk.episode_title}",
                        f"Episode URL: {chunk.episode_url or 'N/A'}",
                        f"Transcript chunk: {chunk.chunk_index}",
                        "Transcript excerpt:",
                        content,
                    ]
                )
            )

        return "\n\n".join(sections)

    @staticmethod
    def _build_citations(
        chunks: list[RetrievalResult],
    ) -> list[SourceCitation]:
        """Convert retrieval results into authoritative citations."""

        return [
            SourceCitation(
                citation_number=index,
                episode_title=chunk.episode_title,
                episode_url=chunk.episode_url,
                chunk_index=chunk.chunk_index,
                similarity=chunk.similarity,
            )
            for index, chunk in enumerate(
                chunks,
                start=1,
            )
        ]

    @staticmethod
    def _clean_answer(answer: str) -> str:
        """Remove accidental model-generated source sections."""

        answer = answer.strip()

        unwanted_sections = [
            "\nReferences:",
            "\nReferences",
            "\nSources:",
            "\nSources",
        ]

        for marker in unwanted_sections:
            if marker in answer:
                answer = answer.split(
                    marker,
                    1,
                )[0].rstrip()

        return answer