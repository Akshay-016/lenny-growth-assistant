from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.models import Artifact, SessionModel
from backend.app.models.schemas import (
    ArtifactCreate,
    ArtifactResponse,
)


router = APIRouter(
    prefix="/api",
    tags=["artifacts"],
)


@router.post(
    "/artifacts",
    response_model=ArtifactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_artifact(
    request: ArtifactCreate,
    session: AsyncSession = Depends(get_db),
):
    # Verify that the session exists.
    session_statement = select(SessionModel).where(
        SessionModel.id == request.session_id
    )

    session_result = await session.execute(
        session_statement
    )

    session_model = session_result.scalar_one_or_none()

    if session_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    artifact = Artifact(
        session_id=request.session_id,
        artifact_type=request.artifact_type,
        title=request.title,
        content=request.content,
    )

    session.add(artifact)

    await session.commit()
    await session.refresh(artifact)

    return artifact


@router.get(
    "/artifacts/{artifact_id}",
    response_model=ArtifactResponse,
)
async def get_artifact(
    artifact_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    statement = select(Artifact).where(
        Artifact.id == artifact_id
    )

    result = await session.execute(statement)

    artifact = result.scalar_one_or_none()

    if artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found.",
        )

    return artifact


@router.get(
    "/sessions/{session_id}/artifacts",
    response_model=list[ArtifactResponse],
)
async def get_session_artifacts(
    session_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    # Verify that the session exists.
    session_statement = select(SessionModel).where(
        SessionModel.id == session_id
    )

    session_result = await session.execute(
        session_statement
    )

    session_model = session_result.scalar_one_or_none()

    if session_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    # Retrieve artifacts belonging to this session.
    artifact_statement = (
        select(Artifact)
        .where(Artifact.session_id == session_id)
        .order_by(Artifact.created_at.desc())
    )

    artifact_result = await session.execute(
        artifact_statement
    )

    return list(artifact_result.scalars().all())