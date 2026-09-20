import asyncio

from backend.app.database import Base, engine
from backend.app.models import (
    Artifact,
    Message,
    SessionModel,
    TranscriptChunk,
)


async def create_tables():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    print("Database tables created successfully.")


if __name__ == "__main__":
    asyncio.run(create_tables())