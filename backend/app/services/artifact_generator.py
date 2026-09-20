"""Grounded artifact generation for Lenny Growth Assistant."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.providers.llm import LLMProvider, get_llm_provider
from backend.app.rag.retriever import (
    RetrievalResult,
    TranscriptRetriever,
)


SUPPORTED_ARTIFACT_TYPES = {
    "framework",
    "checklist",
    "growth_plan",
    "essay",
}


@dataclass(frozen=True)
class ArtifactSource:
    """Source metadata used to ground an artifact."""

    citation_number: int
    episode_title: str
    episode_url: str | None
    chunk_index: int
    similarity: float


@dataclass(frozen=True)
class ArtifactGenerationResult:
    """Result returned by the artifact generation service."""

    content: str
    grounded: bool
    sources: list[ArtifactSource]


class ArtifactGenerator:
    """
    Generate Markdown artifacts grounded in Lenny's Podcast transcripts.

    The transcript knowledge base is the factual boundary. The LLM is
    responsible for writing the artifact, while retrieval owns the evidence.
    """

    def __init__(
        self,
        retriever: TranscriptRetriever | None = None,
        llm_provider: LLMProvider | None = None,
    ):
        self.retriever = retriever or TranscriptRetriever()
        self.llm_provider = llm_provider or get_llm_provider()

    async def generate(
        self,
        request: str,
        session: AsyncSession,
        artifact_type: str,
        top_k: int = 5,
        similarity_threshold: float = 0.65,
    ) -> ArtifactGenerationResult:
        """
        Generate a grounded Markdown artifact.

        Args:
            request: User's description of what should be created.
            session: Database session used for transcript retrieval.
            artifact_type: framework, checklist, growth_plan, or essay.
            top_k: Number of transcript chunks to retrieve.
            similarity_threshold: Minimum retrieval similarity.
        """

        request = request.strip()
        artifact_type = artifact_type.strip().lower()

        if not request:
            raise ValueError(
                "Artifact generation request cannot be empty."
            )

        if artifact_type not in SUPPORTED_ARTIFACT_TYPES:
            supported_types = ", ".join(
                sorted(SUPPORTED_ARTIFACT_TYPES)
            )
            raise ValueError(
                f"Unsupported artifact type: {artifact_type}. "
                f"Supported types: {supported_types}."
            )

        chunks = await self.retriever.search(
            query=request,
            session=session,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )

        if not chunks:
            return ArtifactGenerationResult(
                content=(
                    "I couldn't find enough relevant information in "
                    "Lenny's Podcast transcripts to create this artifact "
                    "reliably."
                ),
                grounded=False,
                sources=[],
            )

        evidence = self._build_evidence(chunks)

        prompt = self._build_prompt(
            request=request,
            artifact_type=artifact_type,
            evidence=evidence,
        )

        system_prompt = self._build_system_prompt(
            artifact_type=artifact_type,
        )

        content = await self.llm_provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            max_tokens=1400,
        )

        content = self._clean_content(content)

        if not content:
            raise RuntimeError(
                "The LLM returned an empty artifact."
            )

        sources = [
            ArtifactSource(
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

        return ArtifactGenerationResult(
            content=content,
            grounded=True,
            sources=sources,
        )

    @staticmethod
    def _build_system_prompt(
        artifact_type: str,
    ) -> str:
        """Build the artifact-specific system instructions."""

        type_instructions = {
            "framework": (
                "Create a practical framework with a clear structure, "
                "principles, steps, and decision guidance."
            ),
            "checklist": (
                "Create a practical checklist with clear, actionable "
                "items grouped into useful sections."
            ),
            "growth_plan": (
                "Create a practical growth plan with goals, priorities, "
                "actions, sequencing, and measurable considerations."
            ),
            "essay": (
                "Create a concise, useful essay with a strong opening, "
                "logical progression, clear headings where useful, and "
                "a practical takeaway."
            ),
        }

        return f"""
You are the artifact-generation component of Lenny Growth Assistant.

The artifact must be grounded ONLY in the supplied Lenny's Podcast
transcript evidence.

Artifact type:
{artifact_type}

{type_instructions[artifact_type]}

Grounding rules:

1. Use only information supported by the supplied transcript evidence.
2. You may synthesize and organize ideas from the evidence.
3. Do not invent facts, statistics, quotations, guest experiences,
   examples, companies, or claims.
4. Do not use outside knowledge.
5. Do not fabricate quotations.
6. Do not invent source URLs.
7. Do not create citation numbers.
8. Do not create a References section.
9. Do not create a Sources section.
10. Do not mention the retrieval process.
11. Return Markdown only.
12. Make the artifact useful and actionable.
13. If the evidence is insufficient, clearly say so instead of inventing
    supporting information.

The application attaches authoritative source metadata separately.
""".strip()

    @staticmethod
    def _build_prompt(
        request: str,
        artifact_type: str,
        evidence: str,
    ) -> str:
        """Build the grounded artifact-generation prompt."""

        return f"""
Create a {artifact_type} based on the user's request below.

USER REQUEST
------------
{request}

TRANSCRIPT EVIDENCE
-------------------
{evidence}

WRITING REQUIREMENTS
--------------------

Create the requested artifact in Markdown.

The artifact should:

- directly address the user's request;
- have a clear and useful structure;
- be practical rather than generic;
- synthesize the supplied transcript evidence;
- avoid unsupported claims;
- avoid fabricated quotations;
- avoid invented statistics or examples;
- avoid outside information.

Do not add a References section.
Do not add a Sources section.
Do not create citation numbers.

Return only the finished Markdown artifact.
""".strip()

    @staticmethod
    def _build_evidence(
        chunks: list[RetrievalResult],
    ) -> str:
        """Convert retrieved transcript chunks into grounded evidence."""

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
    def _clean_content(content: str) -> str:
        """Remove accidental source/reference sections."""

        content = content.strip()

        unwanted_markers = [
            "\nReferences:",
            "\nReferences",
            "\nSources:",
            "\nSources",
        ]

        for marker in unwanted_markers:
            if marker in content:
                content = content.split(
                    marker,
                    1,
                )[0].rstrip()

        return content