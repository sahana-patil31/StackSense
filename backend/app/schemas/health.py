from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str | None = None


class DatabaseHealthResponse(BaseModel):
    status: str
    database: str | None = None


class SystemHealthResponse(BaseModel):
    status: str
    api: str
    database: str
    vector_search: str
    risk_model: str
    embedding_provider: str
    llm: str
