from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


class RepositoryCreate(BaseModel):
    name: str = Field(min_length=1)
    url: Optional[HttpUrl] = None
    provider: Literal["github", "gitlab", "local", "other"] = Field(default="other")
    default_branch: Optional[str] = None


class RepositoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    url: Optional[HttpUrl] = None
    provider: Optional[Literal["github", "gitlab", "local", "other"]] = None
    default_branch: Optional[str] = None


class RepositoryResponse(BaseModel):
    id: str
    name: str
    url: Optional[str] = None
    provider: str
    default_branch: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
