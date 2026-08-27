from contextlib import asynccontextmanager
import json
import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.anomalies import router as anomalies_router
from app.api.routes.auth import router as auth_router
from app.api.routes.code_analysis import router as code_analysis_router
from app.api.routes.health import router as health_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.assistant import router as assistant_router
from app.api.routes.ingestion.commits import router as commits_router
from app.api.routes.ingestion.deployments import router as deployments_router
from app.api.routes.ingestion.events import router as events_router
from app.api.routes.ingestion.overview import router as overview_router
from app.api.routes.ingestion.repositories import router as repositories_router
from app.api.routes.risk import router as risk_router
from app.core.config import get_settings
from app.core.database import Base, engine
from app.models.analysis_run import AnalysisRun
from app.models.anomaly import Anomaly
from app.models.application_event import ApplicationEvent
from app.models.code_entity import CodeEntity
from app.models.code_file import CodeFile
from app.models.code_relationship import CodeRelationship
from app.models.commit import Commit
from app.models.deployment import Deployment
from app.models.deployment_risk_analysis import DeploymentRiskAnalysis
from app.models.incident import Incident
from app.models.ingestion_batch import IngestionBatch
from app.models.project import Project
from app.models.repository import Repository
from app.models.root_cause_analysis import RootCauseAnalysis
from app.models.knowledge_document import KnowledgeDocument
from app.models.conversation import Conversation, ConversationMessage
from app.models.user import User

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        app.state.db_initialized = True
    except SQLAlchemyError as exc:
        app.state.db_initialized = False
        print(f"Database initialization skipped: {exc}")
    yield


app = FastAPI(title="STACKSENSE API", version="0.1.0", lifespan=lifespan)

request_logger = logging.getLogger("stacksense.request")


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    started = time.perf_counter()
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception:
        status_code = 500
        raise
    finally:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        request.app.state.metrics = getattr(request.app.state, "metrics", {"requests": 0, "errors": 0, "latency_ms": 0.0})
        request.app.state.metrics["requests"] += 1
        request.app.state.metrics["latency_ms"] += elapsed_ms
        if status_code >= 400:
            request.app.state.metrics["errors"] += 1
        request_logger.info(json.dumps({"request_id": request_id, "method": request.method, "path": request.url.path, "status": status_code, "duration_ms": elapsed_ms}))
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    return JSONResponse(status_code=422, content={"detail": "Request validation failed", "errors": exc.errors(), "request_id": request_id}, headers={"X-Request-ID": request_id})


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "request_id": request_id}, headers={"X-Request-ID": request_id})


@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "request_id": request_id}, headers={"X-Request-ID": request_id})


@app.get("/api/metrics", include_in_schema=False)
def metrics():
    values = getattr(app.state, "metrics", {"requests": 0, "errors": 0, "latency_ms": 0.0})
    return PlainTextResponse("\n".join([
        "# TYPE stacksense_http_requests_total counter",
        f"stacksense_http_requests_total {values['requests']}",
        "# TYPE stacksense_http_errors_total counter",
        f"stacksense_http_errors_total {values['errors']}",
        "# TYPE stacksense_http_request_latency_ms_sum counter",
        f"stacksense_http_request_latency_ms_sum {values['latency_ms']}",
    ]) + "\n")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(repositories_router)
app.include_router(commits_router)
app.include_router(deployments_router)
app.include_router(events_router)
app.include_router(overview_router)
app.include_router(code_analysis_router)
app.include_router(risk_router)
app.include_router(anomalies_router)
app.include_router(incidents_router)
app.include_router(assistant_router)


