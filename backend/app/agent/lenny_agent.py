"""Agent orchestration for Lenny Growth Assistant.

The agent layer sits between the chat API and the existing RAG system.

Provider behavior:
- Ollama: uses the existing grounded RAG generator for local/demo use.
- Anthropic: uses the Claude Agent SDK with retrieved transcript evidence.

The transcript knowledge base remains the factual boundary for both paths.
"""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.rag.generator import RAGAnswerGenerator
from backend.app.rag.retriever import RetrievalResult, TranscriptRetriever


@dataclass(frozen=True)
class AgentCitation:
    """Citation metadata returned by the agent."""

    citation_number: int
    episode_title: str
    episode_url: str | None
    chunk_index: int
    similarity: float


@dataclass(frozen=True)
class AgentResponse:
    """Response returned by the Lenny agent."""

    answer: str
    grounded: bool
    citations: list[AgentCitation]


class LennyAgent:
    """
    Provider-aware orchestration layer for Lenny Growth Assistant.

    The local Ollama path keeps the existing RAG implementation intact.

    The Anthropic path uses the Claude Agent SDK and supplies retrieved
    transcript evidence directly to Claude so that the model is grounded
    in the Lenny knowledge base.
    """

    def __init__(
        self,
        retriever: TranscriptRetriever | None = None,
        rag_generator: RAGAnswerGenerator | None = None,
        provider_name: str | None = None,
    ):
        settings = get_settings()

        self.provider = (
            provider_name or settings.default_llm_provider
        ).lower()

        self.retriever = retriever or TranscriptRetriever()
        self.rag_generator = rag_generator or RAGAnswerGenerator()

    async def answer(
        self,
        query: str,
        session: AsyncSession,
        top_k: int = 5,
        similarity_threshold: float = 0.65,
        conversation_context: str | None = None,
    ) -> AgentResponse:
        """
        Generate a grounded answer using the configured provider.
        """

        if not query.strip():
            return AgentResponse(
                answer="Please provide a question.",
                grounded=False,
                citations=[],
            )

        if self.provider == "anthropic":
            return await self._answer_with_claude(
                query=query,
                session=session,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                conversation_context=conversation_context,
            )

        # Default/local path.
        #
        # This intentionally preserves the existing RAG implementation
        # because Ollama is the required local/demo provider.
        response = await self.rag_generator.answer(
            query=query,
            session=session,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            conversation_context=conversation_context,
        )

        return AgentResponse(
            answer=response.answer,
            grounded=response.grounded,
            citations=[
                AgentCitation(
                    citation_number=citation.citation_number,
                    episode_title=citation.episode_title,
                    episode_url=citation.episode_url,
                    chunk_index=citation.chunk_index,
                    similarity=citation.similarity,
                )
                for citation in response.citations
            ],
        )

    async def _answer_with_claude(
        self,
        query: str,
        session: AsyncSession,
        top_k: int,
        similarity_threshold: float,
        conversation_context: str | None,
    ) -> AgentResponse:
        """
        Retrieve transcript evidence and ask Claude Agent SDK to synthesize
        a grounded answer from that evidence.
        """

        settings = get_settings()

        if not settings.anthropic_api_key.strip():
            raise RuntimeError(
                "ANTHROPIC_API_KEY is required when "
                "DEFAULT_LLM_PROVIDER=anthropic."
            )

        chunks = await self.retriever.search(
            query=query,
            session=session,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )

        if not chunks:
            return AgentResponse(
                answer=(
                    "I couldn't find enough relevant information in "
                    "Lenny's Podcast transcripts to answer that "
                    "question reliably."
                ),
                grounded=False,
                citations=[],
            )

        evidence = self._build_evidence(chunks)

        prompt = self._build_claude_prompt(
            query=query,
            evidence=evidence,
            conversation_context=conversation_context,
        )

        answer = await self._run_claude(prompt)

        citations = [
            AgentCitation(
                citation_number=index,
                episode_title=chunk.episode_title,
                episode_url=chunk.episode_url,
                chunk_index=chunk.chunk_index,
                similarity=chunk.similarity,
            )
            for index, chunk in enumerate(chunks, start=1)
        ]

        return AgentResponse(
            answer=answer,
            grounded=True,
            citations=citations,
        )

    async def _run_claude(self, prompt: str) -> str:
        """
        Run a single-turn Claude Agent SDK request.

        Tools are intentionally disabled because the Lenny transcript
        retrieval layer is the application's source of truth.
        """

        from claude_agent_sdk import (
            AssistantMessage,
            ClaudeAgentOptions,
            TextBlock,
            query,
        )

        settings = get_settings()

        options = ClaudeAgentOptions(
            model=settings.anthropic_model,
            system_prompt=(
                "You are Lenny Growth Assistant. "
                "Answer the user's question using only the supplied "
                "Lenny transcript evidence. "
                "Do not invent facts, statistics, quotations, "
                "experiences, or sources. "
                "If the evidence is insufficient, say so clearly. "
                "Do not create a References or Sources section because "
                "the application attaches verified source metadata."
            ),
            tools=[],
            max_turns=1,
            permission_mode="dontAsk",
            env={
                "ANTHROPIC_API_KEY": settings.anthropic_api_key,
            },
        )

        text_parts: list[str] = []

        async for message in query(
            prompt=prompt,
            options=options,
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        text_parts.append(block.text)

        answer = "".join(text_parts).strip()

        if not answer:
            raise RuntimeError(
                "Claude Agent SDK returned an empty response."
            )

        return answer

    @staticmethod
    def _build_evidence(
        chunks: list[RetrievalResult],
    ) -> str:
        """
        Convert retrieved chunks into explicit evidence for Claude.
        """

        sections: list[str] = []

        for index, chunk in enumerate(
            chunks,
            start=1,
        ):
            sections.append(
                f"""
EVIDENCE {index}
---------------

Episode:
{chunk.episode_title}

Episode URL:
{chunk.episode_url or "Not available"}

Transcript chunk:
{chunk.chunk_index}

Similarity:
{chunk.similarity:.4f}

TRANSCRIPT:
{chunk.content.strip()}
""".strip()
            )

        return "\n\n---\n\n".join(sections)

    @staticmethod
    def _build_claude_prompt(
        query: str,
        evidence: str,
        conversation_context: str | None,
    ) -> str:
        """
        Build the grounded Claude prompt.
        """

        context_section = ""

        if conversation_context and conversation_context.strip():
            context_section = f"""

CURRENT CONVERSATION CONTEXT
----------------------------
{conversation_context.strip()}
"""

        return f"""
USER QUESTION
-------------
{query.strip()}
{context_section}

TRANSCRIPT EVIDENCE
-------------------
{evidence}

INSTRUCTIONS
------------

Answer the user's question using the supplied transcript evidence.

The transcript evidence is the factual boundary.

You may explain or synthesize information from the evidence, but do not
invent facts, statistics, quotations, experiences, or outside information.

If the supplied evidence does not contain enough information to answer
reliably, clearly say that the available transcript evidence is
insufficient.

Preserve the user's conversational context when it is relevant.

Return only the answer intended for the user.

Do not create a References section.
Do not create a Sources section.
Do not invent citation numbers.

The application will attach verified source metadata separately.
""".strip()