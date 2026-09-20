import asyncio
from pathlib import Path

from sqlalchemy import select

from backend.app.database import AsyncSessionLocal
from backend.app.models import TranscriptChunk
from backend.app.providers.embedding import OllamaEmbeddingProvider
from backend.app.rag.chunker import TranscriptChunker
from backend.app.rag.loader import TranscriptLoader


TRANSCRIPTS_ROOT = Path("data/raw/lennys-podcast-transcripts")

FAILED_TRANSCRIPTS = [
    "matt-mullenweg",
    "matthew-dicks",
    "naomi-gleit",
    "nick-turley",
]


async def embed_with_retry(provider, text, max_attempts=3):
    for attempt in range(1, max_attempts + 1):
        try:
            return await provider.embed(text)
        except Exception as exc:
            print(
                f"      Embedding attempt {attempt}/{max_attempts} failed: "
                f"{type(exc).__name__}: {exc}"
            )

            if attempt == max_attempts:
                raise

            wait_seconds = attempt * 5
            print(f"      Retrying in {wait_seconds} seconds...")
            await asyncio.sleep(wait_seconds)


async def retry_failed_transcripts():
    loader = TranscriptLoader(TRANSCRIPTS_ROOT)
    chunker = TranscriptChunker(chunk_size=650, overlap=100)
    provider = OllamaEmbeddingProvider()

    print("=" * 60)
    print("RETRY FAILED LENNY TRANSCRIPTS")
    print("=" * 60)

    async with AsyncSessionLocal() as session:

        for transcript_name in FAILED_TRANSCRIPTS:

            transcript_path = (
                TRANSCRIPTS_ROOT
                / "episodes"
                / transcript_name
                / "transcript.md"
            )

            print()
            print(f"Processing: {transcript_name}")

            if not transcript_path.exists():
                print(f"  ✗ File not found: {transcript_path}")
                continue

            source_path = str(transcript_path)

            existing_result = await session.execute(
                select(TranscriptChunk.id)
                .where(TranscriptChunk.source_path == source_path)
                .limit(1)
            )

            if existing_result.scalar_one_or_none() is not None:
                print("  ✓ Already exists. Skipping.")
                continue

            document = loader.load_file(transcript_path)
            chunks = chunker.chunk(document.content)

            print(f"  Found {len(chunks)} chunks.")
            print("  Embedding chunks individually with retry protection...")

            inserted = 0

            for index, chunk in enumerate(chunks, start=1):

                print(
                    f"    Embedding chunk {index}/{len(chunks)}...",
                    end=" ",
                    flush=True,
                )

                try:
                    embedding = await embed_with_retry(
                        provider,
                        chunk.content,
                    )

                    transcript_chunk = TranscriptChunk(
                        episode_title=document.title,
                        episode_url=document.episode_url,
                        source_path=source_path,
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                        embedding=embedding,
                    )

                    session.add(transcript_chunk)
                    inserted += 1

                    print("✓")

                except Exception as exc:
                    print(f"✗ {type(exc).__name__}: {exc}")
                    raise

            await session.commit()

            print(
                f"  ✓ Successfully inserted {inserted} chunks "
                f"for {transcript_name}."
            )

    print()
    print("=" * 60)
    print("RETRY COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(retry_failed_transcripts())