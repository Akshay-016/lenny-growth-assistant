import asyncio
import time

from backend.app.database import AsyncSessionLocal
from backend.app.skills.ship30_generator import Ship30Generator


async def main():
    generator = Ship30Generator()

    topic = "How should product teams decide what features to build?"

    print()
    print("=" * 80)
    print("SHIP 30 REAL GENERATION TEST")
    print("=" * 80)
    print()
    print("Topic:", topic)
    print()
    print("Starting generation...")
    print("This will make a real Ollama LLM call.")
    print()

    start_time = time.perf_counter()

    try:
        async with AsyncSessionLocal() as session:
            response = await generator.generate(
                topic=topic,
                session=session,
            )

        elapsed = time.perf_counter() - start_time

        print()
        print("=" * 80)
        print("GENERATION COMPLETE")
        print("=" * 80)

        print()
        print("GROUNDED:", response.grounded)
        print("SOURCES:", len(response.sources))
        print("RETRIEVED CHUNKS:", len(response.retrieved_chunks))
        print("GENERATION TIME: {:.2f} seconds".format(elapsed))

        print()
        print("=" * 80)
        print("ARTICLE")
        print("=" * 80)
        print()

        print(response.article)

        print()
        print("=" * 80)
        print("ARTICLE STATS")
        print("=" * 80)

        word_count = len(response.article.split())

        print("WORD COUNT:", word_count)

        print()
        print("=" * 80)
        print("SOURCES")
        print("=" * 80)

        for source in response.sources:
            print(
                f"{source.source_number}. "
                f"{source.episode_title} | "
                f"similarity={source.similarity:.4f} | "
                f"chunk={source.chunk_index}"
            )

        print()
        print("=" * 80)
        print("REAL GENERATION TEST COMPLETE")
        print("=" * 80)

    except Exception as exc:
        elapsed = time.perf_counter() - start_time

        print()
        print("=" * 80)
        print("GENERATION FAILED")
        print("=" * 80)

        print()
        print("TIME BEFORE FAILURE: {:.2f} seconds".format(elapsed))
        print("ERROR TYPE:", type(exc).__name__)
        print("ERROR:", str(exc))

        raise


if __name__ == "__main__":
    asyncio.run(main())