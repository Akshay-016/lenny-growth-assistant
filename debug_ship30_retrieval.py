import asyncio

from backend.app.database import AsyncSessionLocal
from backend.app.skills.ship30_generator import Ship30Generator


async def main():
    generator = Ship30Generator()

    topic = "How should product teams decide what features to build?"

    async with AsyncSessionLocal() as session:
        retrieved_chunks = await generator.retriever.search(
            query=topic,
            session=session,
            top_k=generator.RETRIEVAL_TOP_K,
        )

        print()
        print("=" * 80)
        print("TOP 20 RETRIEVED CHUNKS")
        print("=" * 80)

        ranked = sorted(
            retrieved_chunks,
            key=lambda result: generator._topic_relevance_score(
                result,
                topic,
            ),
            reverse=True,
        )

        for index, chunk in enumerate(ranked, start=1):
            print()
            print("=" * 80)
            print(f"RANK {index}")
            print("=" * 80)

            print("Episode:", chunk.episode_title)
            print("Chunk:", chunk.chunk_index)
            print("Similarity:", f"{chunk.similarity:.4f}")
            print("Source:", chunk.source_path)
            print("Characters:", len(chunk.content))

            print()
            print("CONTENT:")
            print(chunk.content[:900])

        print()
        print("=" * 80)
        print("CURRENT SELECTION")
        print("=" * 80)

        selected = generator._select_diverse_evidence(
            retrieved_chunks,
            topic,
        )

        for index, chunk in enumerate(selected, start=1):
            print()
            print(
                f"{index}. "
                f"{chunk.episode_title} | "
                f"chunk={chunk.chunk_index} | "
                f"similarity={chunk.similarity:.4f}"
            )

        print()
        print("=" * 80)
        print("DEBUG COMPLETE - NO LLM CALL WAS MADE")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())