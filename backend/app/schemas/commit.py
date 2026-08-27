from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CommitCreate(BaseModel):
    repository_id: str = Field(min_length=1)
    sha: str = Field(min_length=1)
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    message: Optional[str] = None
    committed_at: Optional[datetime | str] = None


class CommitResponse(BaseModel):
    id: str
    repository_id: str
    sha: str
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    message: Optional[str] = None
    committed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
