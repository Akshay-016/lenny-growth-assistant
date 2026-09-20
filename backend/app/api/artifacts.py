from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.models import Artifact, SessionModel
from backend.app.models.schemas import (
    ArtifactCreate,
    ArtifactGenerateRequest,
    ArtifactGenerateResponse,
    ArtifactResponse,
    ArtifactSourceResponse,
)
from backend.app.services.artifact_generator import ArtifactGenerator


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


@router.post(
    "/artifacts/generate",
    response_model=ArtifactGenerateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_artifact(
    request: ArtifactGenerateRequest,
    session: AsyncSession = Depends(get_db),
):
    # ---------------------------------------------------------
    # 1. Verify that the requested session exists.
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # 2. Generate the artifact using grounded transcript
    #    evidence and the configured LLM provider.
    # ---------------------------------------------------------

    generator = ArtifactGenerator()

    try:
        generation_result = await generator.generate(
            request=request.request,
            session=session,
            artifact_type=request.artifact_type,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    # ---------------------------------------------------------
    # 3. Do not save an ungrounded artifact.
    # ---------------------------------------------------------

    if not generation_result.grounded:
        return ArtifactGenerateResponse(
            artifact=None,
            grounded=False,
            sources=[],
        )

    # ---------------------------------------------------------
    # 4. Persist the generated artifact.
    # ---------------------------------------------------------

    artifact = Artifact(
        session_id=request.session_id,
        artifact_type=request.artifact_type,
        title=request.title,
        content=generation_result.content,
    )

    session.add(artifact)

    await session.commit()
    await session.refresh(artifact)

    # ---------------------------------------------------------
    # 5. Return the persisted artifact and verified sources.
    # ---------------------------------------------------------

    sources = [
        ArtifactSourceResponse(
            citation_number=source.citation_number,
            episode_title=source.episode_title,
            episode_url=source.episode_url,
            chunk_index=source.chunk_index,
            similarity=source.similarity,
        )
        for source in generation_result.sources
    ]

    return ArtifactGenerateResponse(
        artifact=artifact,
        grounded=True,
        sources=sources,
    )


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