from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.models import Message, SessionModel
from backend.app.models.schemas import (
    MessageResponse,
    SessionCreate,
    SessionResponse,
)


router = APIRouter(
    prefix="/api/sessions",
    tags=["sessions"],
)


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    request: SessionCreate,
    session: AsyncSession = Depends(get_db),
):
    new_session = SessionModel(
        title=request.title,
    )

    session.add(new_session)

    await session.commit()
    await session.refresh(new_session)

    return new_session


@router.get(
    "",
    response_model=list[SessionResponse],
)
async def list_sessions(
    session: AsyncSession = Depends(get_db),
):
    statement = (
        select(SessionModel)
        .order_by(SessionModel.updated_at.desc())
    )

    result = await session.execute(statement)

    return list(result.scalars().all())


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
)
async def get_session(
    session_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    statement = select(SessionModel).where(
        SessionModel.id == session_id
    )

    result = await session.execute(statement)

    session_model = result.scalar_one_or_none()

    if session_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    return session_model


@router.get(
    "/{session_id}/messages",
    response_model=list[MessageResponse],
)
async def get_session_messages(
    session_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    # ---------------------------------------------------------
    # 1. Verify that the session exists.
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # 2. Retrieve messages belonging to this session.
    # ---------------------------------------------------------

    message_statement = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )

    message_result = await session.execute(
        message_statement
    )

    return list(message_result.scalars().all())