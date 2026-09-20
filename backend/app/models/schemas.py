import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SessionCreate(BaseModel):
    title: str | None = None


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    role: str
    content: str


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    created_at: datetime

class ArtifactCreate(BaseModel):
    session_id: uuid.UUID
    artifact_type: str
    title: str | None = None
    content: str

class ArtifactGenerateRequest(BaseModel):
    session_id: uuid.UUID
    artifact_type: str
    request: str
    title: str | None = None
    top_k: int = 5
    similarity_threshold: float = 0.65

class ArtifactSourceResponse(BaseModel):
    citation_number: int
    episode_title: str
    episode_url: str | None
    chunk_index: int
    similarity: float

class ArtifactGenerateResponse(BaseModel):
    artifact: "ArtifactResponse | None"
    grounded: bool
    sources: list[ArtifactSourceResponse]

class ArtifactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    artifact_type: str
    title: str | None
    content: str
    created_at: datetime