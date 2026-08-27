from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
