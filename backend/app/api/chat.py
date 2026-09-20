from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agent import LennyAgent
from backend.app.database import get_db
from backend.app.models import Message, SessionModel


router = APIRouter(
    prefix="/api",
    tags=["chat"],
)


class ChatRequest(BaseModel):
    session_id: UUID
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
    )
    similarity_threshold: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
    )


class ChatCitation(BaseModel):
    citation_number: int
    episode_title: str
    episode_url: str | None
    chunk_index: int
    similarity: float


class ChatResponse(BaseModel):
    session_id: UUID
    answer: str
    grounded: bool
    citations: list[ChatCitation]


@router.post(
    "/chat",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
    session: AsyncSession = Depends(get_db),
):
    # ---------------------------------------------------------
    # 1. Verify that the requested session exists.
    # ---------------------------------------------------------

    statement = select(SessionModel).where(
        SessionModel.id == request.session_id
    )

    result = await session.execute(statement)

    session_model = result.scalar_one_or_none()

    if session_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    # ---------------------------------------------------------
    # 2. Load recent conversation history.
    #
    # This keeps follow-up questions inside the same session
    # context without mixing conversations between sessions.
    # ---------------------------------------------------------

    history_statement = (
        select(Message)
        .where(
            Message.session_id == request.session_id
        )
        .order_by(
            Message.created_at.desc()
        )
        .limit(8)
    )

    history_result = await session.execute(
        history_statement
    )

    history = list(
        reversed(
            history_result.scalars().all()
        )
    )

    conversation_context = "\n".join(
        f"{message.role.upper()}: {message.content}"
        for message in history
    )

    # ---------------------------------------------------------
    # 3. Send the request through the agent layer.
    # ---------------------------------------------------------

    agent = LennyAgent()

    response = await agent.answer(
        query=request.message,
        session=session,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold,
        conversation_context=(
            conversation_context
            if conversation_context
            else None
        ),
    )

    # ---------------------------------------------------------
    # 4. Save the user's message.
    # ---------------------------------------------------------

    user_message = Message(
        session_id=request.session_id,
        role="user",
        content=request.message,
    )

    # ---------------------------------------------------------
    # 5. Save the assistant's answer.
    # ---------------------------------------------------------

    assistant_message = Message(
        session_id=request.session_id,
        role="assistant",
        content=response.answer,
    )

    session.add(user_message)
    session.add(assistant_message)

    # ---------------------------------------------------------
    # 6. Update session timestamp.
    # ---------------------------------------------------------

    session_model.updated_at = datetime.now(
        timezone.utc
    )

    # ---------------------------------------------------------
    # 7. Commit the conversation.
    # ---------------------------------------------------------

    await session.commit()

    # ---------------------------------------------------------
    # 8. Return structured response and citations.
    # ---------------------------------------------------------

    return ChatResponse(
        session_id=request.session_id,
        answer=response.answer,
        grounded=response.grounded,
        citations=[
            ChatCitation(
                citation_number=citation.citation_number,
                episode_title=citation.episode_title,
                episode_url=citation.episode_url,
                chunk_index=citation.chunk_index,
                similarity=citation.similarity,
            )
            for citation in response.citations
        ],
    )