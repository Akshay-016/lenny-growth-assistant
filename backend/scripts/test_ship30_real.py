import asyncio

from backend.app.database import AsyncSessionLocal
from backend.app.skills.ship30_generator import Ship30Generator


async def main():
    topic = "How should product teams decide what features to build?"

    print("=" * 80)
    print("SHIP 30 FOR 30 — REAL RAG TEST")
    print("=" * 80)
    print()
    print(f"Topic: {topic}")
    print()

    async with AsyncSessionLocal() as session:
        generator = Ship30Generator()

        print("Retrieving Lenny transcript evidence...")
        print()

        response = await generator.generate(
            topic=topic,
            session=session,
        )

    print("=" * 80)
    print("GROUNDING STATUS")
    print("=" * 80)
    print(response.grounded)
    print()

    print("=" * 80)
    print("ARTICLE")
    print("=" * 80)
    print()
    print(response.article)
    print()

    print("=" * 80)
    print("SOURCE METADATA")
    print("=" * 80)

    for source in response.sources:
        print()
        print(f"Source {source.source_number}")
        print(f"Episode: {source.episode_title}")
        print(f"URL: {source.episode_url}")
        print(f"Chunk: {source.chunk_index}")
        print(f"Similarity: {source.similarity:.4f}")
        print(f"Path: {source.source_path}")

    print()
    print("=" * 80)
    print(f"Retrieved chunks: {len(response.retrieved_chunks)}")
    print(f"Sources: {len(response.sources)}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())