"""
Ship 30 for 30 grounded article generator.

This module combines:
- transcript retrieval
- evidence diversification
- topic-focused writing instructions
- the Ship 30 for 30 writing skill
- the configured LLM provider

The generator is responsible for WHAT evidence reaches the writing model.
The Ship 30 skill is responsible for HOW that evidence is written.
"""

import re
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.providers.llm import LLMProvider, get_llm_provider
from backend.app.rag.retriever import RetrievalResult, TranscriptRetriever
from backend.app.skills.ship30 import Ship30For30Skill, get_ship30_skill


@dataclass(frozen=True)
class Ship30Source:
    """
    Source metadata attached to generated Ship 30 content.
    """

    source_number: int
    episode_title: str
    episode_url: str | None
    chunk_index: int
    similarity: float
    source_path: str


@dataclass
class Ship30Response:
    """
    Result returned by the Ship 30 generator.
    """

    article: str
    sources: list[Ship30Source]
    retrieved_chunks: list[RetrievalResult]
    grounded: bool


class Ship30Generator:
    """
    Generate a grounded Ship 30 for 30-style essay.

    Long-form writing needs a broader evidence pool than a normal
    conversational RAG answer. Retrieved evidence is therefore
    diversified and topic-focused before being passed to the writing model.
    """

    RETRIEVAL_TOP_K = 20
    MAX_EVIDENCE_FOR_WRITING = 5
    MAX_CHARS_PER_CHUNK = 900
    MAX_CHUNKS_PER_EPISODE = 2

    MIN_ARTICLE_WORDS = 1000
    TARGET_ARTICLE_WORDS = 1250
    MAX_ARTICLE_WORDS = 1350

    def __init__(
        self,
        retriever: TranscriptRetriever | None = None,
        llm_provider: LLMProvider | None = None,
        skill: Ship30For30Skill | None = None,
    ):
        self.retriever = retriever or TranscriptRetriever()
        self.llm_provider = llm_provider or get_llm_provider()
        self.skill = skill or get_ship30_skill()

    async def generate(
        self,
        topic: str,
        session: AsyncSession,
        additional_context: str | None = None,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
    ) -> Ship30Response:
        """
        Generate a grounded Ship 30 article.

        The transcript knowledge base is the factual boundary.
        If relevant evidence cannot be retrieved, no LLM generation
        is performed.
        """

        topic = topic.strip()

        if not topic:
            return Ship30Response(
                article=(
                    "Please provide a topic or question for the "
                    "Ship 30 for 30 article."
                ),
                sources=[],
                retrieved_chunks=[],
                grounded=False,
            )

        retrieved_chunks = await self.retriever.search(
            query=topic,
            session=session,
            top_k=top_k or self.RETRIEVAL_TOP_K,
            similarity_threshold=similarity_threshold,
        )

        if not retrieved_chunks:
            return Ship30Response(
                article=(
                    "I couldn't find enough relevant information "
                    "in Lenny's Podcast transcripts to create a "
                    "grounded Ship 30 for 30 article on that topic."
                ),
                sources=[],
                retrieved_chunks=[],
                grounded=False,
            )

        selected = self._select_diverse_evidence(
            retrieved_chunks,
            topic,
        )

        evidence = self._build_evidence_context(selected)

        prompt = self.skill.build_prompt(            topic=topic,
            transcript_evidence=evidence,            additional_context=additional_context,
        )

        prompt = self._add_topic_focus_instructions(
            prompt=prompt,
            topic=topic,
        )

        article = await self.llm_provider.generate(
            prompt=prompt,
            system_prompt=self.skill.system_prompt,
            temperature=0.2,
            max_tokens=1800,
        )

        article = self._clean_article(article)

        # llama3.2:3b can stop early even when the prompt requests a
        # 1,100-1,350 word article. If that happens, use a second grounded
        # expansion pass instead of accepting an undersized Ship 30 article.
        if self._word_count(article) < self.MIN_ARTICLE_WORDS:
            article = await self._expand_short_article(
                article=article,
                topic=topic,
                evidence=evidence,
                additional_context=additional_context,
            )
            article = self._clean_article(article)

        article = self._limit_article_length(article)

        sources = self._build_sources(selected)

        return Ship30Response(
            article=article,
            sources=sources,
            retrieved_chunks=selected,
            grounded=True,
        )

    def _select_diverse_evidence(
        self,
        retrieved: list[RetrievalResult],        topic: str,
    ) -> list[RetrievalResult]:
        """
        Select evidence that is semantically relevant, topic-focused,
        and diverse across episodes.

        Semantic similarity is used as the initial retrieval signal.
        A stronger content-based relevance score is then applied so that
        transcript excerpts that actually discuss the requested topic are
        preferred over chunks that are merely about a related subject.

        Duplicate transcript content is skipped so that the same evidence
        cannot consume multiple writing slots just because it appears under
        different episode/source metadata.

        Episode titles are not treated as factual evidence.
        """

        ranked = sorted(
            retrieved,
            key=lambda result: self._topic_relevance_score(
                result,
                topic,
            ),
            reverse=True,
        )

        selected: list[RetrievalResult] = []
        episode_counts: dict[str, int] = {}
        selected_content_keys: set[str] = set()

        for result in ranked:
            if len(selected) >= self.MAX_EVIDENCE_FOR_WRITING:
                break

            episode_key = (
                result.episode_title.strip()
                or result.source_path
            )

            current_count = episode_counts.get(
                episode_key,
                0,
            )

            if current_count >= self.MAX_CHUNKS_PER_EPISODE:
                continue

            content_key = self._evidence_content_key(
                result.content
            )

            if content_key in selected_content_keys:
                continue

            selected.append(result)
            episode_counts[episode_key] = current_count + 1
            selected_content_keys.add(content_key)

        return selected

    def _evidence_content_key(
        self,
        content: str,
    ) -> str:
        """
        Create a normalized fingerprint for transcript content.

        The purpose is to detect duplicate transcript chunks even when
        whitespace or capitalization differs.
        """

        normalized = re.sub(
            r"\s+",
            " ",
            content.strip().lower(),
        )

        return normalized

    def _topic_relevance_score(
        self,
        result: RetrievalResult,
        topic: str,
    ) -> float:
        """
        Score a transcript chunk for direct relevance to the requested topic.

        Semantic similarity remains the base signal.

        Content overlap receives substantially more weight than episode-title
        overlap because episode titles describe the broader conversation and
        are not themselves evidence for the requested claim.

        Multi-word topic concepts receive an additional phrase-match bonus.
        """

        topic_terms = self._topic_terms(topic)

        if not topic_terms:
            return result.similarity

        content_text = result.content.lower()

        content_matches = sum(
            1
            for term in topic_terms
            if re.search(
                rf"\b{re.escape(term)}\b",
                content_text,
            )
        )

        content_overlap = content_matches / len(topic_terms)

        phrase_bonus = 0.0

        topic_phrases = self._topic_phrases(topic)

        for phrase in topic_phrases:
            if phrase in content_text:
                phrase_bonus += 0.06

        return (
            result.similarity
            + (content_overlap * 0.18)
            + phrase_bonus
        )

    def _topic_phrases(
        self,
        topic: str,
    ) -> list[str]:
        """
        Extract useful multi-word phrases from the topic.

        These phrases provide a small additional signal when a transcript
        chunk explicitly discusses the same concept.
        """

        normalized = re.sub(
            r"\s+",
            " ",
            topic.lower(),
        ).strip()

        phrases: list[str] = []

        for phrase in (
            "decide what features to build",
            "features to build",
            "what features to build",
            "product strategy",
            "feature prioritization",
            "feature priority",
            "prioritize features",
            "decide what to build",
            "what to build",
            "product decisions",
            "product roadmap",
        ):
            if phrase in normalized:
                phrases.append(phrase)

        return phrases

    def _topic_terms(
        self,
        topic: str,
    ) -> set[str]:
        """
        Extract useful lexical terms from a topic.
        """

        stop_words = {
            "the",
            "and",
            "for",
            "with",
            "from",
            "that",
            "this",
            "what",
            "when",
            "where",
            "which",
            "who",
            "how",
            "why",
            "can",
            "should",
            "would",
            "could",
            "into",
            "about",
            "your",
            "their",
            "our",
            "are",
            "was",
            "were",
            "is",
            "be",
            "to",
            "of",
            "in",
            "on",
            "a",
            "an",
        }

        words = re.findall(
            r"[a-zA-Z0-9]+",
            topic.lower(),
        )

        return {
            word
            for word in words
            if len(word) >= 3
            and word not in stop_words
        }

    def _build_evidence_context(
        self,
        retrieved: list[RetrievalResult],    ) -> str:
        """
        Convert retrieved transcript chunks into a structured evidence block.

        Episode titles and URLs are supplied only as source metadata.
        The transcript excerpt itself is the factual evidence boundary.
        """

        sections: list[str] = []

        for index, result in enumerate(
            retrieved,
            start=1,
        ):
            content = result.content.strip()

            if len(content) > self.MAX_CHARS_PER_CHUNK:
                content = content[
                    : self.MAX_CHARS_PER_CHUNK
                ].rstrip()

                last_space = content.rfind(" ")

                if last_space > int(
                    self.MAX_CHARS_PER_CHUNK * 0.8
                ):
                    content = content[:last_space]

                content += "..."

            sections.append(
                f"""
EVIDENCE {index}
---------------
SOURCE METADATA:
Episode: {result.episode_title}
Episode URL: {result.episode_url or "Not available"}
Transcript chunk: {result.chunk_index}

FACTUAL TRANSCRIPT EVIDENCE:
{content}
""".strip()
            )

        return "\n\n".join(sections)

    def _add_topic_focus_instructions(
        self,
        prompt: str,
        topic: str,
    ) -> str:
        """
        Add compact topic-specific instructions while giving the local model
        explicit section-length targets.

        The main Ship 30 skill already contains the general writing rules.
        These instructions focus on the requested topic and prevent the local
        model from stopping after a short summary.
        """

        return f"""
FINAL TASK

Topic:
{topic}

Use the supplied transcript evidence as the factual boundary.

Focus the article specifically on the requested topic. Ignore evidence that
does not help answer the topic.

Produce the complete article now.

LENGTH AND STRUCTURE:
- Write 1,100-1,350 words total.
- Target approximately 1,250 words.
- Opening hook and introduction: about 100-140 words.
- Write exactly 5 substantial main sections.
- Each main section should be about 170-200 words.
- Practical Takeaway: about 100-130 words.
- Conclusion: about 70-100 words.
- Do not stop early. If the draft is below 1,100 words, continue developing
  the least-developed sections with transcript-supported explanation before
  ending.
- Use transcript-supported examples where available.
- Keep one clear central argument.
- Return Markdown only.
- Do not add References, Sources, or other resource sections.
- Do not add commentary about the instructions.

{prompt}
""".strip()


    async def _expand_short_article(
        self,
        article: str,
        topic: str,
        evidence: str,
        additional_context: str | None = None,
    ) -> str:
        # Expand only undersized drafts. The transcript evidence remains the
        # factual boundary, and the same 1800-token provider contract is used.
        context = ""
        if additional_context and additional_context.strip():
            context = f"""

CURRENT CONVERSATION CONTEXT
{additional_context.strip()}
"""

        expansion_prompt = f"""
SHIP 30 EXPANSION PASS

Topic:
{topic}

The draft below is shorter than the required minimum. Expand it into a
complete article of approximately 1,100-1,300 words.

IMPORTANT:
- Preserve the draft's central argument and useful structure.
- Keep exactly five substantial main sections.
- Keep a Practical Takeaway and a concise conclusion.
- Add depth, explanation, and transcript-supported examples rather than
  repeating the same sentences.
- Every factual claim must stay within the supplied transcript evidence.
- Do not invent quotations, statistics, experiences, or outside facts.
- Return the complete expanded Markdown article, not commentary.
- Do not add References, Sources, or other resource sections.

TRANSCRIPT EVIDENCE
-------------------
{evidence}

CURRENT DRAFT
-------------
{article}
{context}

Now return the complete expanded article.
""".strip()

        expanded = await self.llm_provider.generate(
            prompt=expansion_prompt,
            system_prompt=self.skill.system_prompt,
            temperature=0.2,
            max_tokens=1800,
        )

        # Never replace a useful draft with a shorter second-pass response.
        if self._word_count(expanded) < self._word_count(article):
            return article

        return expanded.strip()

    def _limit_article_length(
        self,
        article: str,
    ) -> str:
        """
        Keep the final article within the requested maximum word count.

        Trimming is performed at paragraph boundaries where possible so the
        generated article does not end abruptly.
        """

        words = article.split()

        if len(words) <= self.MAX_ARTICLE_WORDS:
            return article.strip()

        paragraphs = re.split(
            r"\n\s*\n",
            article.strip(),
        )

        result: list[str] = []
        current_count = 0

        for paragraph in paragraphs:
            paragraph_words = paragraph.split()

            if (
                current_count + len(paragraph_words)
                <= self.MAX_ARTICLE_WORDS            ):
                result.append(paragraph)
                current_count += len(paragraph_words)
                continue

            remaining = (
                self.MAX_ARTICLE_WORDS
                - current_count
            )

            if remaining >= 40:
                result.append(
                    " ".join(paragraph_words[:remaining])
                )

            break

        return "\n\n".join(result).strip()

    def _word_count(
        self,
        article: str,
    ) -> int:
        """
        Return a simple whitespace-based word count.
        """

        return len(article.split())

    def _build_sources(
        self,
        retrieved: list[RetrievalResult],    ) -> list[Ship30Source]:
        """
        Convert retrieval results into API-facing source metadata.
        """

        return [
            Ship30Source(
                source_number=index,
                episode_title=result.episode_title,
                episode_url=result.episode_url,
                chunk_index=result.chunk_index,
                similarity=result.similarity,
                source_path=result.source_path,
            )
            for index, result in enumerate(
                retrieved,
                start=1,
            )
        ]

    def _clean_article(
        self,
        article: str,
    ) -> str:
        """
        Remove source/reference sections if the model creates them.

        Source metadata is owned by the backend rather than the writing model.
        """

        article = article.strip()

        unwanted_headings = {
            "additional resources",
            "further reading",
            "recommended resources",
            "references",
            "sources",
        }

        lines = article.splitlines()

        cleaned_lines: list[str] = []

        for line in lines:
            normalized = (
                line.strip()
                .lower()
                .lstrip("#")
                .strip()
                .rstrip(":")
                .strip()
            )

            if normalized in unwanted_headings:
                break

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()


def get_ship30_generator(
    retriever: TranscriptRetriever | None = None,
    llm_provider: LLMProvider | None = None,
    skill: Ship30For30Skill | None = None,
) -> Ship30Generator:
    """
    Return a configured Ship 30 generator.
    """