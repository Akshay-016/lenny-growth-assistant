import asyncio

from sqlalchemy import text

from backend.app.database import engine


async def migrate():
    async with engine.begin() as connection:
        await connection.execute(
            text(
                """
                ALTER TABLE transcript_chunks
                ADD COLUMN IF NOT EXISTS source_path VARCHAR(1000);
                """
            )
        )

        await connection.execute(
            text(
                """
                UPDATE transcript_chunks
                SET source_path = 'legacy-test-' || id::text
                WHERE source_path IS NULL;
                """
            )
        )

        await connection.execute(
            text(
                """
                ALTER TABLE transcript_chunks
                ALTER COLUMN source_path SET NOT NULL;
                """
            )
        )

        await connection.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS
                uq_transcript_chunk_source
                ON transcript_chunks (source_path, chunk_index);
                """
            )
        )

    print("Migration completed successfully.")


if __name__ == "__main__":
    asyncio.run(migrate())