from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class IngestionBatchCreate(BaseModel):
    source: str = Field(min_length=1)
    data_type: str = Field(min_length=1)
    status: str = "running"
    records_received: int = 0
    records_inserted: int = 0
    records_failed: int = 0
    error_summary: Optional[str] = None


class IngestionBatchResponse(BaseModel):
    id: str
    source: str
    data_type: str
    status: str
    records_received: int
    records_inserted: int
    records_failed: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_summary: Optional[str] = None

    class Config:
        from_attributes = True


class BulkIngestionSummary(BaseModel):
    received: int
    inserted: int
    duplicates: int = 0
    failed: int = 0
