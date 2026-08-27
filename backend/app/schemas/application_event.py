from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel


class ApplicationEventCreate(BaseModel):
    service_name: Optional[str] = None
    timestamp: Optional[datetime | str] = None
    severity: Optional[str] = None
    event_type: Optional[str] = None
    message: Optional[str] = None
    error_type: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class ApplicationEventResponse(BaseModel):
    id: str
    service_name: Optional[str] = None
    timestamp: Optional[datetime] = None
    severity: Optional[str] = None
    event_type: Optional[str] = None
    message: Optional[str] = None
    error_type: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
