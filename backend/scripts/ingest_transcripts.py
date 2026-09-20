import asyncio
from pathlib import Path

from sqlalchemy import select

from backend.app.database import AsyncSessionLocal
from backend.app.models import TranscriptChunk
from backend.app.rag.ingestion import (
    TranscriptIngestionService,
)


TRANSCRIPTS_ROOT = Path(
    "data/raw/lennys-podcast-transcripts"
)


async def ingest_all_transcripts():
    service = TranscriptIngestionService(
        TRANSCRIPTS_ROOT
    )

    transcripts = service.loader.find_transcripts()

    total = len(transcripts)

    print("=" * 60)
    print("LENNY'S PODCAST TRANSCRIPT INGESTION")
    print("=" * 60)
    print(f"Found {total} transcript files.")
    print("Processing all remaining transcripts.")
    print()

    total_inserted_chunks = 0
    total_skipped_transcripts = 0
    total_errors = 0
    processed_new = 0

    async with AsyncSessionLocal() as session:

        for transcript_path in transcripts:

            source_path = str(transcript_path)

            existing_result = await session.execute(
                select(TranscriptChunk.id)
                .where(
                    TranscriptChunk.source_path
                    == source_path
                )
                .limit(1)
            )

            already_ingested = (
                existing_result.scalar_one_or_none()
                is not None
            )

            if already_ingested:
                total_skipped_transcripts += 1
                continue

            processed_new += 1

            print(
                f"[NEW {processed_new}] "
                f"{transcript_path}"
            )

            try:
                inserted = (
                    await service.store_document(
                        transcript_path,
                        session,
                    )
                )

                if inserted > 0:
                    print(
                        f"  ✓ Inserted "
                        f"{inserted} chunks."
                    )

                    total_inserted_chunks += inserted

                else:
                    print(
                        "  - No new chunks."
                    )

            except Exception as exc:
                print(
                    f"  ✗ ERROR: "
                    f"{type(exc).__name__}: {exc}"
                )

                total_errors += 1

            print()

    print("=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    print(
        f"Total transcript files: "
        f"{total}"
    )
    print(
        f"New transcripts processed: "
        f"{processed_new}"
    )
    print(
        f"Previously ingested transcripts: "
        f"{total_skipped_transcripts}"
    )
    print(
        f"New chunks inserted: "
        f"{total_inserted_chunks}"
    )
    print(
        f"Errors: {total_errors}"
    )
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(
        ingest_all_transcripts()
    )