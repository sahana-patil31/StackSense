from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class DeploymentCreate(BaseModel):
    repository_id: str = Field(min_length=1)
    commit_sha: Optional[str] = None
    environment: Literal["development", "staging", "production"]
    status: Literal["pending", "running", "success", "failed", "cancelled"]
    service_name: Optional[str] = None
    deployed_at: Optional[datetime | str] = None


class DeploymentResponse(BaseModel):
    id: str
    repository_id: str
    commit_sha: Optional[str] = None
    environment: str
    status: str
    service_name: Optional[str] = None
    deployed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
