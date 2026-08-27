from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings
from app.schemas.health import DatabaseHealthResponse, HealthResponse, SystemHealthResponse

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="healthy", service="stacksense-api")


@router.get("/db", response_model=DatabaseHealthResponse)
def database_health(db: Session = Depends(get_db)) -> DatabaseHealthResponse:
    try:
        db.execute(text("SELECT 1"))
        return DatabaseHealthResponse(status="healthy", database="connected")
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc


@router.get("/system", response_model=SystemHealthResponse)
def system_health(db: Session = Depends(get_db)) -> SystemHealthResponse:
    database = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        database = "unhealthy"
    settings = get_settings()
    return SystemHealthResponse(
        status="healthy" if database == "healthy" else "degraded",
        api="healthy",
        database=database,
        vector_search="healthy",
        risk_model="healthy",
        embedding_provider=settings.embedding_provider,
        llm=settings.llm_provider,
    )
