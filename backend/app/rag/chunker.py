from dataclasses import dataclass


@dataclass
class TextChunk:
    content: str
    chunk_index: int


class TranscriptChunker:
    """
    Splits transcript text into overlapping word-based chunks.

    Target:
        500–800 tokens approximately
        100-token overlap

    We use words as a lightweight approximation for tokens during
    ingestion. The resulting chunks are validated by character/word
    boundaries rather than splitting in the middle of words.
    """

    def __init__(
        self,
        chunk_size: int = 650,
        overlap: int = 100,
    ):
        if chunk_size <= overlap:
            raise ValueError(
                "chunk_size must be greater than overlap"
            )

        if overlap < 0:
            raise ValueError(
                "overlap cannot be negative"
            )

        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[TextChunk]:
        words = text.split()

        if not words:
            return []

        chunks: list[TextChunk] = []

        start = 0
        chunk_index = 0

        while start < len(words):
            end = min(
                start + self.chunk_size,
                len(words),
            )

            chunk_words = words[start:end]

            content = " ".join(chunk_words).strip()

            if content:
                chunks.append(
                    TextChunk(
                        content=content,
                        chunk_index=chunk_index,
                    )
                )

            if end >= len(words):
                break

            start = end - self.overlap
            chunk_index += 1

        return chunks